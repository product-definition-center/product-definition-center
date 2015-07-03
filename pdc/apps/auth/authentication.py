#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework.authentication import TokenAuthentication


class TokenAuthenticationWithChangeSet(TokenAuthentication):
    def authenticate(self, request):
        auth_result = super(TokenAuthenticationWithChangeSet,
                            self).authenticate(request)
        # NOTE(xchu): The `auth_result` can be `None` if uncorrect
        #             authorization header is privided or nothing privided.
        if auth_result is None:
            return auth_result

        # NOTE(xchu): Update request.changeset.author if the author is None;
        #             That's because if we use `TokenAuthentication`,
        #             DRF do the TokenAuthentication after the request passed
        #             `ChangesetMiddleware` and all other Django middlewares.
        #             Which means that we will not have the user until `authenticate`
        #             here.
        if hasattr(request, "changeset") and request.changeset.author is None:
            # the `auth_result` is `None` or a (user, token) tuple.
            request.changeset.author = auth_result[0]
        return auth_result
