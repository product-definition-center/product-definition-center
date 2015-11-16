#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from itertools import groupby
import json
import os.path

from productmd.rpms import Rpms
from productmd.images import Images, Image

from django.conf import settings
from kobo.django.views.generic import DetailView, SearchView
from django.views.generic import View
from django.forms.formsets import formset_factory
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status, serializers
from django.db.models import Q
from django.http import Http404

from contrib.bulk_operations import bulk_operations

from pdc.apps.package.serializers import RPMSerializer
from pdc.apps.common.models import Arch
from pdc.apps.common.hacks import bool_from_native, convert_str_to_bool, as_dict
from pdc.apps.common.viewsets import (ChangeSetCreateModelMixin,
                                      StrictQueryParamMixin,
                                      NoEmptyPatchMixin,
                                      ChangeSetDestroyModelMixin,
                                      ChangeSetModelMixin,
                                      MultiLookupFieldMixin)
from pdc.apps.release.models import Release
from .models import (Compose, VariantArch, Variant, ComposeRPM, OverrideRPM,
                     ComposeImage, ComposeRPMMapping, ComposeAcceptanceTestingState,
                     ComposeTree)
from .forms import (ComposeSearchForm, ComposeRPMSearchForm, ComposeImageSearchForm,
                    ComposeRPMDisableForm, OverrideRPMForm, VariantArchForm, OverrideRPMActionForm)
from .serializers import ComposeSerializer, OverrideRPMSerializer, ComposeTreeSerializer
from .filters import ComposeFilter, OverrideRPMFilter, ComposeTreeFilter
from . import lib


class ComposeListView(SearchView):
    form_class = ComposeSearchForm
    queryset = Compose.objects.all() \
        .select_related('release', 'compose_type') \
        .prefetch_related('linked_releases').order_by('id')
    allow_empty = True
    template_name = "compose_list.html"
    context_object_name = "compose_list"
    paginate_by = settings.ITEMS_PER_PAGE


class ComposeDetailView(DetailView):
    queryset = Compose.objects.select_related('release', 'compose_type') \
        .prefetch_related('linked_releases', 'variant_set__variantarch_set',
                          'variant_set__variantarch_set__arch',
                          'variant_set__variant_type')
    pk_url_kwarg = "id"
    template_name = "compose_detail.html"


class ComposeRPMListView(SearchView):
    form_class = ComposeRPMSearchForm

    allow_empty = True
    template_name = "compose_rpm_list.html"
    context_object_name = "compose_rpm_list"
    paginate_by = settings.ITEMS_PER_PAGE

    def get_queryset(self):
        urlargs = self.request.resolver_match.kwargs
        variants = Variant.objects.filter(compose=urlargs["id"])
        variant = variants.filter(variant_uid=urlargs["variant"])
        if "arch" in urlargs:
            arch = Arch.objects.get(name=urlargs["arch"])
        variant_arch = VariantArch.objects.filter(variant=variant)
        if "arch" in urlargs:
            variant_arch = variant_arch.get(arch=arch)
        packages = ComposeRPM.objects.filter(variant_arch=variant_arch)
        query = self.get_form(self.form_class).get_query(self.request)
        packages = packages.filter(query)
        packages = packages.extra(order_by=["rpm__name", "rpm__version", "rpm__release",
                                            "rpm__epoch", "rpm__arch"])
        return packages

    def get_context_data(self, *args, **kwargs):
        context = super(ComposeRPMListView, self).get_context_data(*args, **kwargs)

        urlargs = self.request.resolver_match.kwargs
        compose = str(Compose.objects.get(pk=urlargs["id"]))

        context["compose"] = compose
        context["variant"] = urlargs["variant"]
        if "arch" in urlargs:
            context["arch"] = urlargs["arch"]

        return context


class ComposeImageListView(SearchView):
    form_class = ComposeImageSearchForm

    allow_empty = True
    template_name = "compose_image_list.html"
    context_object_name = "compose_image_list"
    paginate_by = settings.ITEMS_PER_PAGE

    def get_queryset(self):
        urlargs = self.request.resolver_match.kwargs
        variants = Variant.objects.filter(compose=urlargs["id"])
        variant = variants.filter(variant_uid=urlargs["variant"])
        variant_arch = VariantArch.objects.filter(variant=variant)
        if "arch" in urlargs:
            arch = Arch.objects.get(name=urlargs["arch"])
            variant_arch = variant_arch.get(arch=arch)
        images = ComposeImage.objects.filter(variant_arch=variant_arch)
        query = self.get_form(self.form_class).get_query(self.request)
        images = images.filter(query)
        return images

    def get_context_data(self, *args, **kwargs):
        context = super(ComposeImageListView, self).get_context_data(*args, **kwargs)

        urlargs = self.request.resolver_match.kwargs
        compose = str(Compose.objects.get(pk=urlargs["id"]))

        context["compose"] = compose
        context["variant"] = urlargs["variant"]
        if "arch" in urlargs:
            context["arch"] = urlargs["arch"]

        return context


class RPMOverrideFormView(View):
    """
    This view supports GET and POST methods. On GET, it displays the overrides
    form, on POST it shows a preview of submitted data.
    """

    def __init__(self, *args, **kwargs):
        super(RPMOverrideFormView, self).__init__(*args, **kwargs)

        self.checkbox_form_factory = formset_factory(ComposeRPMDisableForm, extra=0)
        self.override_form_factory = formset_factory(OverrideRPMForm, extra=0)
        self.variant_form_factory = formset_factory(VariantArchForm, extra=1)
        self.override_v_form_factory = formset_factory(OverrideRPMForm, extra=0)

    def _create_initial_form_data(self, release_id):
        """
        Obtain data from database and mangle it to appropriate form. This
        method populates two instance attributes, `initial_checkboxes` and
        `initial_overrides`. Both contain a list of dicts. Note that the lists
        are sorted first by value of `variant` key, then by `arch` and lastly
        by `rpm_name` and `rpm_arch`.
        """
        release = Release.objects.get(release_id=release_id)
        self.compose = release.get_latest_compose()
        mapping, useless = self.compose.get_rpm_mapping(self.request.GET['package'],
                                                        release=release)

        checkboxes = []
        overs = set()
        for variant, arch, rpm_name, rpm_data in mapping:
            checkboxes.append({"variant": variant,
                               "arch": arch,
                               "rpm_name": rpm_name,
                               "rpm_arch": rpm_data['rpm_arch'],
                               "included": rpm_data['included'],
                               "override": rpm_data['override']})
            overs.add((variant, arch))
        self.initial_checkboxes = checkboxes
        self.initial_overrides = sorted({"variant": x[0], "arch": x[1]} for x in overs)
        self.useless_overrides = useless

    def _populate_context(self):
        """
        Use precomputed forms to populate the context used for rendering
        response. The forms MUST have initial values filled in even on POST
        request, as the data is used to sort the fields.

        The main item in context is under the `forms` key. It is a list of
        tuples (Variant, Arch, Checkbox-Form-List, New-Override-Form-List).

        Some of the keys in context are not used in templates, but are accessed
        when testing. These are `override_forms`, `override_v_forms` and
        `variant_forms`.
        """
        checkbox_forms = [(variant, arch, list(forms)) for (variant, arch), forms
                          in groupby(self.checkbox_form, lambda x: (x.initial['variant'], x.initial['arch']))]

        # forms :: Map (Variant, Arch) ([ComposerRPMDisableForm], [OverrideRPMForm])
        forms = {}
        for (variant, arch, checks) in checkbox_forms:
            forms[(variant, arch)] = (checks, [])
        for new_form in self.override_form:
            variant = new_form.initial.get('variant') or new_form['variant'].value()
            arch = new_form.initial.get('arch') or new_form['arch'].value()
            forms.get((variant, arch), ([], []))[1].append(new_form)

        var_forms = {}
        for new_variant in self.variant_form:
            num_id = new_variant.prefix.split('-')[1]
            var_forms[num_id] = (new_variant, [])
        for new_form in self.override_v_form:
            var_forms[new_form['new_variant'].value()][1].append(new_form)

        self.context = {
            'package': self.request.GET['package'],
            'override_forms': self.override_form,
            'override_v_forms': self.override_v_form,
            'variant_forms': self.variant_form,
            "forms": [(a, b, c, d) for ((a, b), (c, d)) in sorted(forms.items())],
            "vararch_forms": var_forms.values(),
            "management_forms": [x.management_form for x in self.formsets],
            "has_errors": any(x.errors for x in self.formsets),
            "useless_overrides": [i for i in self.useless_overrides if i.do_not_delete],
            'compose': self.compose,
        }

    def _create_formsets(self):
        """
        Create formsets as instance attributes. The we are processing a POST
        request, the forms will use data supplied by the request, otherwise it
        will fall back to initial data.

        There are four formsets:

        checkbox_form
        :    forms used to disable existing packages
        override_form
        :    forms used to create new overrides for existing Variant.Arch
        variant_form
        :    forms used to create new Variant.Arch
        override_v_form
        :    forms used to create new overrides for new Variant.Arch
        """
        args = [self.request.POST] if self.request.method == 'POST' else []
        self.checkbox_form = self.checkbox_form_factory(*args,
                                                        initial=self.initial_checkboxes,
                                                        prefix="checks")
        self.override_form = self.override_form_factory(*args,
                                                        initial=self.initial_overrides,
                                                        prefix="news")
        self.variant_form = self.variant_form_factory(*args, prefix="vararch")
        self.override_v_form = self.override_v_form_factory(*args,
                                                            initial=[{"new_variant": "0"}],
                                                            prefix="for_new_vararch")
        self.formsets = [self.checkbox_form, self.override_form, self.variant_form, self.override_v_form]

    @csrf_exempt
    def get(self, request, release_id):
        self._create_initial_form_data(release_id)
        self._create_formsets()
        self._populate_context()
        self.context.update({"release_id": release_id})

        return render(request, 'overrides_form.html', self.context)

    def _prepare_preview(self, release_id):
        package = self.request.GET['package']
        if not all([x.is_valid() for x in self.formsets]):
            return False

        initial_data = []

        def stage(type, args, include, initial_data=initial_data):
            data = {'release_id': release_id,
                    'srpm_name': package,
                    'action': type,
                    'variant': args['variant'],
                    'arch': args['arch'],
                    'rpm_name': args['rpm_name'],
                    'rpm_arch': args['rpm_arch'],
                    'include': include,
                    }
            initial_data.append(data)

        for form in self.checkbox_form:
            data = form.cleaned_data
            if form.initial['included'] == data['included']:
                # No change in this form
                continue

            # ComposeRPM disabled by override should be included again.
            if form.initial['override'] == 'delete' and data['included']:
                stage('delete', data, False)

            # Override creating a new package should be disabled.
            if form.initial['override'] == 'create' and not data['included']:
                stage('delete', data, True)

            # ComposeRPM should be disabled.
            if form.initial['override'] == 'orig' and not data['included']:
                stage('create', data, False)

        for data in self.override_form.cleaned_data:
            if data['rpm_name']:
                stage('create', data, True)

        for data in self.override_v_form.cleaned_data:
            if data['rpm_name']:
                vararch_idx = data['new_variant']
                data['variant'] = self.variant_form.cleaned_data[vararch_idx]['variant']
                data['arch'] = self.variant_form.cleaned_data[vararch_idx]['arch']

                stage('create', data, True)

        for record in initial_data:
            try:
                orpm = OverrideRPM.objects.get(release__release_id=release_id,
                                               variant=record['variant'],
                                               arch=record['arch'],
                                               rpm_name=record['rpm_name'],
                                               rpm_arch=record['rpm_arch'])
                record['do_not_delete'] = orpm.do_not_delete
                record['comment'] = orpm.comment
                if orpm.do_not_delete and orpm.include != record['include']:
                    record['warning'] = ('This override already exists with different inclusion. ' +
                                         'Will modify override with do_not_delete set.')
            except OverrideRPM.DoesNotExist:
                pass

        form_factory = formset_factory(OverrideRPMActionForm, extra=0)
        forms = form_factory(initial=initial_data)

        self.context = {
            'actions': json.dumps(initial_data, indent=2),
            'compressed': json.dumps(initial_data),
            'forms': forms,
            'num_forms': len(forms.forms),
            'package': package,
            'release_id': release_id,
        }
        return True

    def post(self, request, release_id):
        package = request.GET['package']
        args = {"release_id": release_id, "package": package}
        release = Release.objects.get(release_id=release_id)

        self._create_initial_form_data(release_id)
        self._create_formsets()

        if request.POST.get('preview_submit', False):
            factory = formset_factory(OverrideRPMActionForm, extra=0)
            initial_data = json.loads(request.POST['initial_data'])
            form = factory(request.POST, initial=initial_data)
            if form.is_valid():
                merge_data(initial_data, form.cleaned_data)
                _apply_changes(request, release, initial_data)
                messages.success(request, 'Data was successfully saved.')
                return redirect(request.path + '?package=' + package)

            self.context = {
                'actions': json.dumps(initial_data, indent=2),
                'compressed': request.POST['initial_data'],
                'forms': form,
                'has_errors': True,
                'num_forms': len(form.forms),
                'package': package,
                'release_id': release_id,
            }
            return render(request, 'overrides_preview.html', self.context)
        else:
            if self._prepare_preview(release_id):
                return render(request, 'overrides_preview.html', self.context)

        self._populate_context()
        self.context.update(args)

        return render(request, 'overrides_form.html', self.context)


def merge_data(actions, forms):
    for act in actions:
        for form in forms:
            if dict_equal_on(act, form, ['variant', 'arch', 'rpm_name', 'rpm_arch']):
                act['do_not_delete'] = form['do_not_delete']
                act['comment'] = form['comment']


def dict_equal_on(d1, d2, keys):
    """
    Return True iff both dicts have all the requested keys with the same
    values.

    >>> dict_equal_on({1: 'a', 2: 'b'}, {1: 'a', 2: 'c'}, [1, 2])
    False
    >>> dict_equal_on({'a': 1}, {'b': 2}, [])
    True
    """
    if not keys:
        return True
    return d1.get(keys[0]) == d2.get(keys[0]) and dict_equal_on(d1, d2, keys[1:])


def _apply_changes(request, release, changes):
    """
    Apply each change to update an override. The `changes` argument should be a
    list of values suitable for `OverrideRPM.update_object` method. Each
    perfomed change is logged.
    """
    for change in changes:
        pk, old_val, new_val = OverrideRPM.update_object(change['action'], release, change)
        request.changeset.add('OverrideRPM', pk, old_val, new_val)


class ComposeViewSet(StrictQueryParamMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    """
    API endpoint that allows querying composes. `GET` request to this URL will
    return the list of composes, each with link to the actual compose.

    Each compose was built for a specific release. This relation is captured by
    the `release` property, which contains an identifier of the release. A
    compose can also be linked to arbitrary number of other releases. These
    links are accessible via the `linked_releases` property.

    The compose data contain a key `rpm_mapping_template` which can be
    transformed into a URL for obtaining and modifying RPM mapping. The
    template contains a string `{{package}}` which should be replaced with the
    package name you are interested in.
    """
    queryset = Compose.objects.all().order_by('id')
    serializer_class = ComposeSerializer
    filter_class = ComposeFilter
    lookup_field = 'compose_id'
    lookup_value_regex = '[^/]+'

    def filter_queryset(self, qs):
        """
        If the viewset instance has attribute `order_queryset` set to True,
        this method returns a list of composes ordered according to *productmd*
        library. Otherwise it will return an unsorted queryset. (It is not
        possible to sort unconditionally as get_object() will at some point
        call this method and fail unless it receives a QuerySet instance.)
        """
        qs = super(ComposeViewSet, self).filter_queryset(qs)
        if getattr(self, 'order_queryset', False):
            return sorted(qs)
        return qs

    def retrieve(self, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:compose-detail:compose_id$

        __Response__:

        %(SERIALIZER)s
        """
        return super(ComposeViewSet, self).retrieve(*args, **kwargs)

    def list(self, *args, **kwargs):
        """
        Get a list of all composes. The composes are ordered first by the
        release for which they were build (by their short and version).
        Composes in the same release are ordered by date, type and respin.

        __Method__: GET

        __URL__: $LINK:compose-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
        """
        self.order_queryset = True
        return super(ComposeViewSet, self).list(*args, **kwargs)

    def update_arch_testing_status(self, data):
        compose_id = self.kwargs[self.lookup_field]
        for variant_uid in data:
            variant_data = as_dict(data[variant_uid], name=variant_uid)
            for arch_name, status_name in variant_data.iteritems():
                try:
                    var_arch = VariantArch.objects.get(arch__name=arch_name,
                                                       variant__variant_uid=variant_uid,
                                                       variant__compose__compose_id=compose_id)
                    state = ComposeAcceptanceTestingState.objects.get(name=status_name)
                except VariantArch.DoesNotExist:
                    raise serializers.ValidationError(
                        {'rtt_tested_architectures':
                         '%s.%s not in compose %s.' % (variant_uid, arch_name, compose_id)}
                    )
                except ComposeAcceptanceTestingState.DoesNotExist:
                    raise serializers.ValidationError(
                        {'rtt_tested_architectures': '"%s" is not a known testing status for %s.%s.'
                         % (status_name, variant_uid, arch_name)}
                    )
                self.request.changeset.add('ComposeVariantArch', var_arch.pk,
                                           json.dumps({"rtt_testing_status": var_arch.rtt_testing_status.name}),
                                           json.dumps({"rtt_testing_status": status_name}))
                var_arch.rtt_testing_status = state
                var_arch.save()

    def update(self, request, *args, **kwargs):
        # This method is used by bulk update and partial update, but should not
        # be called directly.
        if not kwargs.get('partial', False):
            return self.http_method_not_allowed(request, *args, **kwargs)

        if not request.data:
            return NoEmptyPatchMixin.make_response()

        updatable_keys = set(['acceptance_testing', 'linked_releases', 'rtt_tested_architectures'])
        if set(request.data.keys()) - updatable_keys:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'detail': 'Only these properties can be updated: %s'
                                  % ', '.join(updatable_keys)})

        arch_testing_status = as_dict(request.data.pop('rtt_tested_architectures', {}),
                                      name='rtt_tested_architectures')
        self.update_arch_testing_status(arch_testing_status)

        old_data = ComposeSerializer(instance=self.get_object(), context={'request': request}).data
        response = super(ComposeViewSet, self).update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            request.changeset.add('Compose', self.object.pk,
                                  json.dumps({'acceptance_testing': old_data['acceptance_testing']}),
                                  json.dumps({'acceptance_testing': response.data['acceptance_testing']}))
            request.changeset.add('Compose', self.object.pk,
                                  json.dumps({'linked_releases': old_data['linked_releases']}),
                                  json.dumps({'linked_releases': response.data['linked_releases']}))
            # Add message
            if hasattr(request._request, '_messagings'):
                request._request._messagings.append(
                    ('.compose',
                     json.dumps({'action': 'update',
                                 'compose_id': self.object.compose_id,
                                 'from': old_data,
                                 'to': response.data})))
        return response

    def perform_update(self, serializer):
        # To log changes, we need updated instance saved somewhere.
        self.object = serializer.save()

    def bulk_update(self, *args, **kwargs):
        """
        It is possible to perform bulk partial update on composes with `PATCH`
        method. The input must be a JSON object with compose identifiers as
        keys. Values for these keys should be in the same format as when
        updating a single compose.
        """
        return bulk_operations.bulk_update_impl(self, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Only some compose fields can be modified by this call. These are
        `acceptance_testing`, `linked_releases` and `rtt_tested_architectures`.
        Trying to change anything else will result in 400 BAD REQUEST response.

        __Method__: PATCH

        __URL__: $LINK:compose-detail:compose_id$

        __Data__:

            {
                "acceptance_testing": string,
                "linked_releases": [string],
                "rtt_tested_architectures": object
            }

        If the same release is specified in `linked_release` multiple times, it
        will be saved only once.

        The `rtt_tested_architectures` should be a mapping in the form of
        `{variant: {arch: status}}`. Whatever is specified will be saved in
        database, trees not mentioned will not be modified. Specifying variant
        or architecture that does not exist will result in error.

        __Response__:
        same as for retrieve
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class ComposeRPMView(StrictQueryParamMixin, viewsets.GenericViewSet):
    lookup_field = 'compose_id'
    lookup_value_regex = '[^/]+'
    queryset = ComposeRPM.objects.none()    # Required for permissions

    def create(self, request):
        """
        Import RPMs.

        __Method__: POST

        __URL__: $LINK:composerpm-list$

        __Data__:

            {
                "release_id": string,
                "composeinfo": composeinfo,
                "rpm_manifest": rpm_manifest
            }

        The `composeinfo` and `rpm_manifest` values should be actual JSON
        representation of composeinfo and rpm manifest, as stored in
        `composeinfo.json` and `rpm-manifest.json` files.

        __Example__:

            $ curl -H 'Content-Type: application/json' -X POST \\
                -d "{\\"composeinfo\\": $(cat /path/to/composeinfo.json), \\
                     \\"rpm_manifest\\": $(cat /path/to/rpm-manifest.json), \\
                     \\"release_id\\": \\"release-1.0\\" }" \\
                $URL:composerpm-list$

        Note that RPM manifests tend to be too large to supply the data via
        command line argument and using a temporary file becomes necessary.

            $ { echo -n '{"composeinfo": '; cat /path/to/composeinfo.json
            > echo -n ', "rpm_manifest": '; cat /path/to/rpm-manifest.json
            > echo -n ', "release_id": "release-1.0" }' ; } >post_data.json
            $ curl -H 'Content-Type: application/json' -X POST -d @post_data.json \\
                $URL:composerpm-list$

        You could skip the file and send the data directly to `curl`. In such a
        case use `-d @-`.
        """
        data = request.data
        errors = {}
        for key in ('release_id', 'composeinfo', 'rpm_manifest'):
            if key not in data:
                errors[key] = ["This field is required"]
        if errors:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=errors)
        lib.compose__import_rpms(request, data['release_id'], data['composeinfo'], data['rpm_manifest'])
        return Response(status=status.HTTP_201_CREATED)

    def retrieve(self, request, **kwargs):
        """
        **Method**: `GET`

        **URL**: $LINK:composerpm-detail:compose_id$

        This API end-point allows retrieving RPM manifest for a given compose.
        It will return the exact same data as was imported.
        """
        compose = get_object_or_404(Compose, compose_id=kwargs['compose_id'])
        crpms = ComposeRPM.objects.filter(variant_arch__variant__compose=compose) \
                          .select_related('variant_arch__variant', 'variant_arch__arch', 'rpm', 'path') \
                          .prefetch_related('sigkey', 'content_category')
        manifest = Rpms()
        manifest.compose.date = compose.compose_date.strftime('%Y%m%d')
        manifest.compose.id = compose.compose_id
        manifest.compose.respin = compose.compose_respin
        manifest.compose.type = compose.compose_type.name
        for crpm in crpms:
            arch = crpm.variant_arch.arch.name

            path = (os.path.join(crpm.path.path, crpm.rpm.filename)
                    if crpm.path and crpm.rpm.filename
                    else None)

            if crpm.rpm.arch == 'src':
                srpm_nevra = None
            else:
                srpm_nevra = crpm.rpm.srpm_nevra

            manifest.add(
                arch=arch,
                variant=crpm.variant_arch.variant.variant_uid,
                nevra=crpm.rpm.nevra,
                path=path,
                sigkey=crpm.sigkey.key_id if crpm.sigkey else None,
                category=crpm.content_category.name,
                srpm_nevra=srpm_nevra,
            )

        return Response(manifest.serialize({}))


class ComposeRPMMappingView(StrictQueryParamMixin,
                            viewsets.GenericViewSet):
    """
    This API endpoint allows viewing and modification of RPM mapping. The
    overrides applied in this view (if not suppressed) come from the release
    the compose was built for.
    """
    lookup_field = 'package'
    queryset = ComposeRPM.objects.none()    # Required for permissions
    extra_query_params = ('disable_overrides', 'perform')

    def retrieve(self, request, **kwargs):
        """
        __URL__: $LINK:composerpmmapping-detail:compose_id:package$

        Returns a JSON representing the RPM mapping. There is an optional query
        parameter `?disable_overrides=1` which returns the raw mapping not
        affected by any overrides.
        """
        compose = get_object_or_404(Compose, compose_id=kwargs['compose_id'])
        mapping, _ = compose.get_rpm_mapping(kwargs['package'],
                                             bool(request.query_params.get('disable_overrides', False)))
        return Response(mapping.get_pure_dict())

    def partial_update(self, request, **kwargs):
        """
        __URL__: $LINK:composerpmmapping-detail:compose_id:package$

        Unlike other API end-points, patching RPM mapping requires you to specify all the fields. The request data
        should be a list of objects where each object has exactly the keys listed in documentation below. Only `include`
        field can be left out if `action` is not `create`.

            [
                {
                    "action":           <str>,
                    "release_id":       <str>,
                    "variant":          <str>,
                    "arch":             <str>,
                    "srpm_name":        <str>,
                    "rpm_name":         <str>,
                    "rpm_arch":         <str>,
                    "include":          <bool>,     # create only
                    "comment":          <str>,
                    "do_not_delete":    <bool>
                }
            ]
        """
        compose = get_object_or_404(Compose, compose_id=kwargs['compose_id'])
        _apply_changes(request, compose.release, request.data)
        return Response(status=204)

    def update(self, request, **kwargs):
        """
        __URL__: $LINK:composerpmmapping-detail:compose_id:package$

        Allows updating the RPM mapping by using a `PUT` request with data
        containing new mapping. PDC will compute changes between current
        mapping and the requested one. The response contains a list of changes
        suitable for partial update via `PATCH` method.

        By default, no changes are performed on the server. If you add
        `?perform=1` query string parameter, the changes will actually be saved
        in database as well as returned.
        """
        compose = get_object_or_404(Compose, compose_id=kwargs['compose_id'])
        mapping, _ = compose.get_rpm_mapping(kwargs['package'])
        new_mapping = ComposeRPMMapping(data=request.data)
        changes = mapping.compute_changes(new_mapping)
        if bool(request.query_params.get('perform', False)):
            _apply_changes(request, compose.release, changes)
        return Response(changes)


class ComposeImageView(StrictQueryParamMixin,
                       viewsets.GenericViewSet):
    queryset = ComposeImage.objects.none()  # Required for permissions
    lookup_field = 'compose_id'
    lookup_value_regex = '[^/]+'

    def create(self, request):
        """
        Import images.

        __Method__: POST

        __URL__: $LINK:composeimage-list$

        __Data__:

            {
                "release_id": string,
                "composeinfo": composeinfo,
                "image_manifest": image_manifest
            }

        The `composeinfo` and `image_manifest` values should be actual JSON
        representation of composeinfo and image manifest, as stored in
        `composeinfo.json` and `image-manifest.json` files.

        __Example__:

            $ curl -H 'Content-Type: application/json' -X POST \\
                -d "{\\"composeinfo\\": $(cat /path/to/composeinfo.json), \\
                     \\"image_manifest\\": $(cat /path/to/image-manifest.json), \\
                     \\"release_id\\": \\"release-1.0\\" }" \\
                $URL:composeimage-list$
        """
        data = request.data
        errors = {}
        for key in ('release_id', 'composeinfo', 'image_manifest'):
            if key not in data:
                errors[key] = ["This field is required"]
        if errors:
            return Response(status=400, data=errors)
        lib.compose__import_images(request, data['release_id'], data['composeinfo'], data['image_manifest'])
        return Response(status=201)

    def retrieve(self, request, **kwargs):
        """
        __Method__: `GET`

        __URL__: $LINK:composeimage-detail:compose_id$

        This API end-point allows retrieving RPM manifest for a given compose.
        It will return the exact same data as was imported.
        """
        compose = get_object_or_404(Compose, compose_id=kwargs['compose_id'])
        cimages = ComposeImage.objects.filter(variant_arch__variant__compose=compose)

        manifest = Images()
        manifest.compose.date = compose.compose_date.strftime('%Y%m%d')
        manifest.compose.id = compose.compose_id
        manifest.compose.respin = compose.compose_respin
        manifest.compose.type = compose.compose_type.name

        for cimage in cimages:
            im = Image(None)
            im.path = os.path.join(cimage.path.path, cimage.image.file_name)
            im.arch = cimage.image.arch
            im.bootable = cimage.image.bootable
            im.mtime = cimage.image.mtime
            im.size = cimage.image.size
            im.volume_id = cimage.image.volume_id
            im.type = cimage.image.image_type.name
            im.format = cimage.image.image_format.name
            im.arch = cimage.image.arch
            im.disc_number = cimage.image.disc_number
            im.disc_count = cimage.image.disc_count
            im.checksums = {'sha256': cimage.image.sha256}
            if cimage.image.md5:
                im.checksums['md5'] = cimage.image.md5
            if cimage.image.sha1:
                im.checksums['sha1'] = cimage.image.sha1
            im.implant_md5 = cimage.image.implant_md5
            manifest.add(cimage.variant_arch.variant.variant_uid, cimage.variant_arch.arch.name, im)

        return Response(manifest.serialize({}))


class ComposeImportImagesView(StrictQueryParamMixin, viewsets.GenericViewSet):
    # TODO: remove this class after next release
    queryset = ComposeImage.objects.none()  # Required for permissions

    def create(self, request):
        """
        This end-point is deprecated. Use $LINK:composeimage-list$ instead.
        """
        data = request.data
        errors = {}
        for key in ('release_id', 'composeinfo', 'image_manifest'):
            if key not in data:
                errors[key] = ["This field is required"]
        if errors:
            return Response(status=400, data=errors)
        lib.compose__import_images(request, data['release_id'], data['composeinfo'], data['image_manifest'])
        return Response(status=201)


class ReleaseOverridesRPMViewSet(StrictQueryParamMixin,
                                 mixins.ListModelMixin,
                                 ChangeSetCreateModelMixin,
                                 ChangeSetDestroyModelMixin,
                                 viewsets.GenericViewSet):
    """
    Create, search or delete RPM overrides for specific release. The release is
    referenced by its `release_id`.
    """

    serializer_class = OverrideRPMSerializer
    queryset = OverrideRPM.objects.all().order_by('id')
    filter_class = OverrideRPMFilter

    def create(self, *args, **kwargs):
        """
        __Method__: POST

        __URL__: $LINK:overridesrpm-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

            $ curl -H 'Content-Type: application/json' "$URL:overridesrpm-list$" \\
                -X POST -d '{"variant": "Client", "arch": "x86_64", "srpm_name": "bash", \\
                             "rpm_name": "bash-doc", "rpm_arch": "src", "include": true, \\
                             "release": "release-1.0"}'
            {
                "id": 1,
                "release": "release-1.0",
                "variant": "Client",
                "arch": "x86_64",
                "srpm_name": "bash",
                "rpm_name": "bash-doc",
                "rpm_arch": "src",
                "include": true,
                "comment": "",
                "do_not_delete": false
            }
        """
        return super(ReleaseOverridesRPMViewSet, self).create(*args, **kwargs)

    def list(self, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:overridesrpm-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

            $ curl -H 'Content-Type: application/json' "$URL:overridesrpm-list$"
            {
                "previous": null,
                "next": null,
                "count": 1,
                "results": [{
                    "id": 1,
                    "do_not_delete": false,
                    "release": "release-1.0",
                    "variant": "Client",
                    "arch": "x86_64",
                    "srpm_name": "bash",
                    "rpm_name": "bash-doc",
                    "rpm_arch": "src",
                    "include": true,
                    "comment": ""
                }]
            }
        """
        return super(ReleaseOverridesRPMViewSet, self).list(*args, **kwargs)

    def destroy(self, *args, **kwargs):
        """
        Delete a particular override.

        __Method__: DELETE

        __URL__: $LINK:overridesrpm-detail:id$
        """
        return super(ReleaseOverridesRPMViewSet, self).destroy(*args, **kwargs)

    def bulk_destroy(self, *args, **kwargs):
        """
        There are two ways to invoke this call. Both require a request body. In
        one case you can only delete a list of specific overrides, in the other
        you clear all overrides on a given release.

        __Method__: DELETE

        __URL__: $LINK:overridesrpm-list$

        __Data__:

            [id]

        or

            {
                "release":  string,
                "force":    bool        # optional, default false
            }

        __Response__:

        For deleting a list of specific objects there is no output.

        When clearing all overrides, a list of deleted objects is returned.

        __Example__:

            $ curl -H 'Content-Type: application/json' "$URL:overridesrpm-list$" \\
                -X DELETE -d '[1, 15, 29]'

        Clearing all overrides.

            $ curl -H 'Content-Type: application/json' "$URL:overridesrpm-list$" \\
                -X DELETE -d '{ "release": "release-1.0", "force": false }'
            [
                {
                    "id": 1,
                    "do_not_delete": false,
                    "release": "release-1.0",
                    "variant": "Client",
                    "arch": "x86_64",
                    "srpm_name": "bash",
                    "rpm_name": "bash-magic",
                    "rpm_arch": "src",
                    "include": true,
                    "comment": ""
                }
            ]

        """
        data = self.request.data
        if isinstance(data, dict):
            keys = set(data.keys())
            if keys - {'force'} != {'release'}:
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data=["Allowed keys are release and force (optional, default false)."])
            release_obj = get_object_or_404(Release, release_id=data["release"])
            data = self._clear(release_obj, data)
            if data:
                return Response(status=status.HTTP_200_OK, data=data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'detail': 'Not found.'})

        if isinstance(data, list):
            return bulk_operations.bulk_destroy_impl(self, *args, **kwargs)

        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data=['Bulk delete expects either a list or object.'])

    def _clear(self, release_obj, args):
        query = Q(release=release_obj)

        if not bool_from_native(args.get("force", "False")):
            query &= Q(do_not_delete=False)

        queryset = OverrideRPM.objects.filter(query)
        result = []
        for override in queryset:
            serializer = self.serializer_class(override)
            self.request.changeset.add('OverrideRPM', override.pk, serializer.data, 'null')
            result.append(serializer.data)
        queryset.delete()
        return result


class FilterBugzillaProductsAndComponents(StrictQueryParamMixin,
                                          viewsets.ReadOnlyModelViewSet):
    """
    This API endpoint allows listing bugzilla products and components with RPM's nvr.
    """
    queryset = ComposeRPM.objects.none()    # Required for permissions
    extra_query_params = ('nvr', )

    def list(self, request):
        """
        __Method__: GET

        __URL__: $LINK:bugzilla-list$

        __Query params__:

        The `nvr` is always required.

        %(FILTERS)s

        __Response__:

            [
                {
                    "bugzilla_component": [
                        string,
                        ...
                    ],
                    "bugzilla_product": string
                },
                ...
            ]

        __Example__:

            $ curl -H 'Content-Type: application/json' "$URL:bugzilla-list$?nvr=GConf2-3.2.6-8.el7"
            [
                {
                    "bugzilla_component": [
                        "GConf1", "GConf2"
                    ],
                    "bugzilla_product": "Fedora"
                }
            ]
        """

        nvr = request.query_params.get('nvr', None)
        if nvr is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'detail': 'The nvr is required.'})
        try:
            result = lib.find_bugzilla_products_and_components_with_rpm_nvr(nvr)
        except ValueError, ex:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'detail': str(ex)})
        else:
            return Response(status=status.HTTP_200_OK, data=result)


class FindComposeMixin(object):

    def _filter_by_compose_type(self, qs):
        if self.included_compose_type:
            qs = qs.filter(compose_type__name=self.included_compose_type)
        if self.excluded_compose_type:
            qs = qs.exclude(compose_type__name=self.excluded_compose_type)
        return qs

    def _get_composes_for_release(self):
        result = []
        composes = Compose.objects.filter(release__release_id=self.release_id)
        composes = self._filter_by_compose_type(composes)
        result = self._get_result(composes, result)
        return result

    def _get_composes_for_product_version(self):
        result = []
        all_composes = []
        releases = Release.objects.filter(product_version__product_version_id=self.product_version)
        for release in releases:
            composes = Compose.objects.filter(release=release)
            composes = self._filter_by_compose_type(composes)
            all_composes.extend(composes)
        result = self._get_result(all_composes, result)
        return result

    def _get_result(self, composes, result):
        if self.latest:
            compose = max(composes) if composes else None
            if compose:
                self._construct_result(compose, result)
        else:
            for compose in sorted(composes):
                self._construct_result(compose, result)
        return result

    def _construct_result(self, compose, result):
        rpms = compose.get_rpms(self.rpm_name)
        result.append({'compose': compose.compose_id,
                       'packages': self._packages_output(rpms)})
        return result

    def _packages_output(self, rpms):
        """
        Output packages with unicode or dict
        """
        packages = [unicode(rpm) for rpm in rpms]
        return (packages
                if not self.to_dict
                else [RPMSerializer(rpm, exclude_fields=['dependencies']).data for rpm in rpms])

    def _get_query_param_or_false(self, request, query_str):
        value = request.query_params.get(query_str)
        if value:
            value = convert_str_to_bool(value)
        else:
            value = False
        setattr(self, query_str, value)

    def _get_older_compose(self):
        compose = get_object_or_404(Compose, compose_id=self.compose_id)
        current_rpms = set(r.sort_key for r in compose.get_rpms(self.rpm_name))
        # Find older composes for same release (not including this one)
        composes = (Compose.objects
                    # Get only older composes
                    .exclude(compose_date__gt=compose.compose_date)
                    # Only composes in the same product
                    .filter(release__short=compose.release.short)
                    # Which have the requested rpm in some version
                    .filter(variant__variantarch__composerpm__rpm__name=self.rpm_name)
                    # Keep only composes from the release that requested
                    # compose belongs to, or GA releases. This way, after R-1.1
                    # it goes to R-1.0, but not R-1.0-updates.
                    .filter(Q(release__release_type__short='ga') | Q(release=compose.release))
                    .exclude(id=compose.id)
                    .distinct())
        composes = self._filter_by_compose_type(composes)
        latest = None
        for compose in sorted(composes, reverse=True):
            rpms = compose.get_rpms(self.rpm_name)
            # Does compose have a version not in current compose?
            if set(r.sort_key for r in rpms) - current_rpms:
                latest = compose
                break
        if not latest:
            raise Http404('No older compose with earlier version of RPM')
        return {
            'compose': latest.compose_id,
            'packages': self._packages_output(rpms)
        }


class FindComposeByReleaseRPMViewSet(StrictQueryParamMixin, FindComposeMixin, viewsets.GenericViewSet):
    """
    This API endpoint allows finding all composes that contain the package
    (and include its version) for a given release and srpm_name
    """
    queryset = ComposeRPM.objects.none()    # Required for permissions
    extra_query_params = ('included_compose_type', 'excluded_compose_type', 'latest', 'to_dict')

    def list(self, request, **kwargs):
        """
        This method allows listing all (compose, package) pairs for a given
        release and RPM name.

        The ordering of composes is performed by the *productmd* library. It
        first compares compose date, then compose type
        (`test` < `nightly` < `production`) and lastly respin.

        `latest` is optional parameter. If it is provided, and the value is True, it will
        return a single pair with the latest compose and its version of the packages.

        `to_dict` is optional parameter, accepted values (True, 'true', 't', 'True', '1'),
        or (False, 'false', 'f', 'False', '0'). If it is provided, and the value is True,
        packages' format will be as a dict.


        __Method__: GET

        __URL__: $LINK:findcomposebyrr-list:release_id:rpm_name$

        __Query params__:

        %(FILTERS)s


        __Response__:

            [
                {
                    "compose": string,
                    "packages": [string]
                },
                ...
            ]

        The list is sorted by compose: oldest first.
        """
        self.included_compose_type = request.query_params.get('included_compose_type')
        self.excluded_compose_type = request.query_params.get('excluded_compose_type')
        self._get_query_param_or_false(request, 'latest')
        self._get_query_param_or_false(request, 'to_dict')
        self.release_id = kwargs.get('release_id')
        self.rpm_name = kwargs.get('rpm_name')
        return Response(self._get_composes_for_release())


class FindOlderComposeByComposeRPMViewSet(StrictQueryParamMixin, FindComposeMixin, viewsets.GenericViewSet):
    """
    This API endpoint allows finding the latest compose older than specified compose
    which contains a different version of the specified package.
    """
    queryset = ComposeRPM.objects.none()    # Required for permissions
    extra_query_params = ('included_compose_type', 'excluded_compose_type', 'to_dict')

    def list(self, request, **kwargs):
        """
        This method is to find the latest compose older than specified compose
        which contains a different version of the specified package when given a
        compose and a package.

        The ordering of composes is performed by the *productmd* library. It
        first compares compose date, then compose type
        (`test` < `nightly` < `production`) and lastly respin.
        This method will find the latest one according to above sequence.

        `to_dict` is optional parameter, accepted values (True, 'true', 't', 'True', '1'),
        or (False, 'false', 'f', 'False', '0'). If it is provided, and the value is True,
        packages' format will be as a dict.


        __Method__: GET

        __URL__: $LINK:findoldercomposebycr-list:compose_id:rpm_name$

        __Query params__:

        %(FILTERS)s

        __Response__:

            [
                {
                    "compose": string,
                    "packages": [string]
                },
                ...
            ]

        The list is sorted by compose: oldest first.
        """
        self.included_compose_type = request.query_params.get('included_compose_type')
        self.excluded_compose_type = request.query_params.get('excluded_compose_type')
        self._get_query_param_or_false(request, 'to_dict')
        self.compose_id = kwargs.get('compose_id')
        self.rpm_name = kwargs.get('rpm_name')
        return Response(self._get_older_compose())


class FindComposeByProductVersionRPMViewSet(StrictQueryParamMixin, FindComposeMixin, viewsets.GenericViewSet):
    """
    This API endpoint allows finding all composes that contain the package
    (and include its version) for a given product_version and srpm_name
    """
    queryset = ComposeRPM.objects.none()    # Required for permissions
    extra_query_params = ('included_compose_type', 'excluded_compose_type', 'latest', 'to_dict')

    def list(self, request, **kwargs):
        """
        This method allows listing all (compose, package) pairs for a given
        product_version and RPM name.

        The ordering of composes is performed by the *productmd* library. It
        first compares compose date, then compose type
        (`test` < `nightly` < `production`) and lastly respin.

        `latest` is optional parameter. If it is provided, and the value is True, it will
        return a single pair with the latest compose and its version of the packages.

        `to_dict` is optional parameter, accepted values (True, 'true', 't', 'True', '1'),
        or (False, 'false', 'f', 'False', '0'). If it is provided, and the value is True,
        packages' format will be as a dict.


        __Method__: GET

        __URL__: $LINK:findcomposesbypvr-list:product_version_id:rpm_name$

        __Query params__:

        %(FILTERS)s


        __Response__:

            [
                {
                    "compose": string,
                    "packages": [string]
                },
                ...
            ]

        The list is sorted by compose: oldest first.
        """
        self.included_compose_type = request.query_params.get('included_compose_type')
        self.excluded_compose_type = request.query_params.get('excluded_compose_type')
        self._get_query_param_or_false(request, 'latest')
        self._get_query_param_or_false(request, 'to_dict')
        self.product_version = kwargs.get('product_version')
        self.rpm_name = kwargs.get('rpm_name')
        return Response(self._get_composes_for_product_version())


class FindComposeWithOlderPackageViewSet(StrictQueryParamMixin, FindComposeMixin,
                                         viewsets.ReadOnlyModelViewSet):
    """
    This API endpoint allows finding composes with different version of a
    package. The other use-case that it serves gives for a release a list of
    composes with versions of included packages.
    """
    queryset = ComposeRPM.objects.none()    # Required for permissions
    extra_query_params = ('release', 'compose', 'rpm_name', 'to_dict', 'product_version', 'included_compose_type',
                          'excluded_compose_type', 'latest')

    def list(self, request):
        """
        This endpoint is deprecated. Please use instead:
        $LINK:findcomposebyrr-list:release_id:rpm_name$,
        $LINK:findoldercomposebycr-list:compose_id:rpm_name$,
        $LINK:findcomposesbypvr-list:product_version:rpm_name$
        """
        self.rpm_name = request.query_params.get('rpm_name')
        self.release_id = request.query_params.get('release')
        self.compose_id = request.query_params.get('compose')
        self.product_version = request.query_params.get('product_version')
        self.included_compose_type = request.query_params.get('included_compose_type')
        self.excluded_compose_type = request.query_params.get('excluded_compose_type')
        self._get_query_param_or_false(request, 'to_dict')
        self._get_query_param_or_false(request, 'latest')

        if not self.rpm_name:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'detail': 'The rpm_name is required.'})
        if self.release_id:
            return Response(self._get_composes_for_release())
        if self.compose_id:
            return Response(self._get_older_compose())
        if self.product_version:
            return Response(self._get_composes_for_product_version())
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={'detail': 'One of product_version, release or compose argument is required.'})


class ComposeTreeViewSet(ChangeSetModelMixin,
                         StrictQueryParamMixin,
                         MultiLookupFieldMixin,
                         viewsets.GenericViewSet):
    """
    API endpoint that allows querying compose-variant-arch relevant to location.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """
    queryset = ComposeTree.objects.all()
    serializer_class = ComposeTreeSerializer
    filter_class = ComposeTreeFilter
    lookup_fields = (
        ('compose__compose_id', r'[^/]+'),
        ('variant__variant_uid', r'[^/]+'),
        ('arch', r'[^/]+'),
        ('location__short', r'[^/]+'),
    )

    def list(self, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:composetreelocations-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
        """
        return super(ComposeTreeViewSet, self).list(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        __Method__: POST

        __URL__: $LINK:composetreelocations-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

         * *synced_content*: $LINK:contentdeliverycontentcategory-list$

        __Response__: Same as input data.

        __NOTE__:
        If synced_content is omitted, all content types are filled in.
        """
        if not request.data.get("synced_content"):
            request.data["synced_content"] = ['binary', 'debug', 'source']
        return super(ComposeTreeViewSet, self).create(request, *args, **kwargs)

    def retrieve(self, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:composetreelocations-detail:compose_id}/{variant_uid}/{arch}/{location$

        __Response__:

        %(SERIALIZER)s
        """
        return super(ComposeTreeViewSet, self).retrieve(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        # This method is used by bulk update and partial update, but should not
        # be called directly.
        if not kwargs.get('partial', False):
            return self.http_method_not_allowed(request, *args, **kwargs)

        if not request.data:
            return NoEmptyPatchMixin.make_response()

        updatable_keys = set(['scheme', 'url', 'synced_content'])
        if set(request.data.keys()) - updatable_keys:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'detail': 'Only these properties can be updated: %s'
                                  % ', '.join(updatable_keys)})

        return super(ComposeTreeViewSet, self).update(request, *args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        """
        It is possible to perform bulk partial update on composetreelocation with `PATCH`
        method. The input must be a JSON object with composetreelocation identifiers as
        keys. Values for these keys should be in the same format as when
        updating a single composetreelocation.
        """
        return bulk_operations.bulk_update_impl(self, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Only some composetreelocation fields can be modified by this call. They are
        `scheme`, `synced_content` and `url`. Trying to change anything else
        will result in 400 BAD REQUEST response.

        __Method__: PATCH

        __URL__: $LINK:composetreelocations-detail:compose_id}/{variant_uid}/{arch}/{location$

        __Data__:

            {
                "scheme": string,
                "synced_content": [string],
                "url": string
            }

        If the same content category is specified in `synced_content` multiple times, it
        will be saved only once.

        __Response__:
        same as for retrieve
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__:
        DELETE

        __URL__: $LINK:composetreelocations-detail:compose_id}/{variant_uid}/{arch}/{location$

        __Response__:

            STATUS: 204 NO CONTENT
        """
        return super(ComposeTreeViewSet, self).destroy(request, *args, **kwargs)
