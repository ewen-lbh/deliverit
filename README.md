# deliverit

Makes releasing versions a breeze.

## Installation

```shell
pip install git+https://github.com/ewen-lbh/deliverit
```

deliverit cannot be posted on PyPI.org yet because I'm using my own fork of [chachacha](https://pypi.org/project/chachacha) that fixes a [serious bug preventing users with dashes in their name to use the module at all](https://github.com/aogier/chachacha/issues/25). But it seems like [PyPI does not allow git dependencies when publishing modules](https://stackoverflow.com/questions/54887301/how-can-i-use-git-repos-as-dependencies-for-my-pypi-package). If you want this package to be on pypi.org, go comment/react on aogier/chachacha#25 and [my associated PR](https://github.com/aogier/chachacha/pull/26) so that @aogier can merge it and release it in the next official version of chachacha.
