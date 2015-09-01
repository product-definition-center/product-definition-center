import os.path

from tito.release import CoprReleaser
from tito.common import run_command, find_git_root, tito_config_dir, info_out
from tito.compat import RawConfigParser


class CoprUserReleaser(CoprReleaser):

    def _load_user_config(self):
        """
        Try to load copr user configs if any
        # 1. copr config file should be located at `~/.config/copr`
        # or
        # 2. user defined should be stored in `copr_user.conf`
        #    next to `releasers.conf`
        """
        config = RawConfigParser()
        config.add_section('copr-user')
        config.set('copr-user', 'ssh_key', '~/.ssh/id_rsa')

        copr_conf = os.path.expanduser("~/.config/copr")
        if os.path.exists(copr_conf):
            config.read(copr_conf)
            config.set('copr-user', 'username', config.get('copr-cli', 'username'))

        tito_dir = os.path.join(find_git_root(), tito_config_dir())
        copr_local = os.path.join(tito_dir, "copr_user.conf")
        if os.path.exists(copr_local):
            config.read(copr_local)

        if not config.has_option('copr-user', 'username'):
            raise Exception("Can not load username from '~/.config/copr' and 'copr_user.conf'")

        return config

    def _submit_build(self, executable, koji_opts, tag, srpm_location):
        """ Copy srpm to remote destination and submit it to Copr """
        cmd = self.releaser_config.get(self.target, "upload_command")
        url = self.releaser_config.get(self.target, "remote_location")
        if self.srpm_submitted:
            srpm_location = self.srpm_submitted
        srpm_base_name = os.path.basename(srpm_location)

        copr_user_config = self._load_user_config()
        # e.g. "scp -i %(private_key)s %(srpm)s %(user)s@my.web.com:public_html/my_srpm/"
        cmd_upload = cmd % {"srpm": srpm_location,
                            "user": copr_user_config.get("copr-user", "username"),
                            "private_key": copr_user_config.get("copr-user", "ssh_key")}
        cmd_submit = "/usr/bin/copr-cli build %s %s%s" % (
            self.releaser_config.get(self.target, "project_name"),
            url % {'user': copr_user_config.get("copr-user", "username")},
            srpm_base_name)

        if self.dry_run:
            self.print_dry_run_warning(cmd_upload)
            self.print_dry_run_warning(cmd_submit)
            return
        # TODO: no error handling when run_command fails:
        if not self.srpm_submitted:
            print("Uploading src.rpm.")
            print(run_command(cmd_upload))
            self.srpm_submitted = srpm_location
        info_out("Submiting build into %s." % self.NAME)
        print(run_command(cmd_submit))
