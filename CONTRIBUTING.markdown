# Contributing to PDC

We welcome all contributions from bug fixes to documentation improvements. If
you want to help, feel free to open a pull request.


## Pull Requests

When you submit a pull request, it is likely that there will be some feedback
requesting changes. When that happens, please update your code accordingly (or
convince us that we are wrong) and upload new version.

It is OK to rebase and squash commits in a pull request. For some changes it
makes sense to be split into multiple separate commits, but generally we don't
want to have a commit *Add feature X* followed by *Fix review comments about
feature X*. In such case, it should be a single commit.


## Merging pull requests

We would like to maintain clean and readable history. Therefore, here are some
guidelines on how to merge proposed pull requests.

When you want to merge a pull request, make sure that the patches are against
`master` branch and not some commit in history:

    $ git checkout feature-branch
    $ git rebase master
    $ git checkout master

After rebasing, you may want to force push the same branch to GitHub.

If the pull request consists of a single commit, rebase it on top of `master`,
merge using fast-forward and push by hand. This will avoid creating a merge
commit (which makes very little sense for a one-commit pull request).

    $ git merge --ff-only feature-branch
    $ python manage.py test
    $ git push origin master

If you pushed the rebased branch, GitHub will automatically mark the pull
request as merged. If you did not push, you have to do it manually. A link to
the commit on `master` branch in a comment is nice, but not required.

If the pull request had multiple commits, merge commit makes sense as it shows
that these commits belong together. In this case again rebase the patches on
`master`, but merge with `--no-ff`. Another option is to push the **rebased**
branch to GitHub and use the merge button. Doing it by hand has the advantage
that you can check what you did.

    $ git merge --no-ff feature-branch
    $ python manage.py test
    $ git push origin master

With this workflow, the history will remain completely linear for requests with
single commit. For requests with multiple commits, there will be *merge
bubbles* showing which commits belong to the pull requests, but they will not
overlap.

    *   c539758 Merge branch 'another-feature'
    |\  
    | * 172eadd Another feature patch 3/3
    | * f85a21a Another feature patch 2/3
    | * 880cf7b Another feature patch 1/3
    |/  
    *   8e1b9df New feature in single patch
    *   e7e3975 Single patch bug fix
    *   7b24b27 Merge branch 'awesome-feature'
    |\  
    | * 06a8491 Add new feature patch 2/2
    | * 6fc1af8 Add new feature patch 1/2
    |/  
    * 5fe48e2 Initial import
