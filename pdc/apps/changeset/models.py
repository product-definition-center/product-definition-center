#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.db import models
from django.conf import settings


class Changeset(models.Model):
    """
    Changeset groups changes together. Changes added via the `add` method are
    not stored immediately. The actual saving is postponed until the `commit`
    method is called. That is done in the middleware, therefore there is no
    need to actually commit from any other method.
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    requested_on = models.DateTimeField()
    committed_on = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        self.tmp_changes = []
        super(Changeset, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return u"changeset-%s" % self.id

    def add(self, target_class, target_id, old_value, new_value):
        """
        Record a change. The `target_class` and `target_id` specify an object
        that was changed, rest of arguments give original and new value.

        If the old and new values are the same, this is a no-op. Logging that
        nothing in fact changed is useless.
        """
        if old_value != new_value:
            self.tmp_changes.append(Change(target_class=target_class.lower(),
                                           target_id=target_id,
                                           old_value=old_value,
                                           new_value=new_value))

    def reset(self):
        """
        Remove all changes from this changeset.
        """
        self.tmp_changes = []

    def commit(self):
        """
        Commit changeset into database. If there are no changes associated with
        this changeset, nothing will be savd.
        """
        if self.tmp_changes:
            self.save()
            for change in self.tmp_changes:
                change.changeset = self
                change.save()

    @property
    def duration(self):
        return self.committed_on - self.requested_on


class Change(models.Model):
    changeset = models.ForeignKey(Changeset)
    target_class = models.CharField(max_length=200)
    target_id = models.PositiveIntegerField()
    old_value = models.TextField()
    new_value = models.TextField()

    def __unicode__(self):
        return u"change-%s" % self.id

    def is_insert(self):
        """Check if a change is an insertion."""
        return self.old_value == 'null' and self.new_value != 'null'

    def is_delete(self):
        """Check if a change is an deletion."""
        return self.old_value != 'null' and self.new_value == 'null'

    def is_update(self):
        """Check if a change is an update."""
        return self.old_value != 'null' and self.new_value != 'null'
