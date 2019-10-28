# Contributing to stories-api

## 1. Git and Github Guidelines

### 1.1. Branching
-   There is one mainline branch that will track our environment builds (`master`). If a new piece of work is to be deployed to our application environments, a pull request needs to be made to merge any development branches into `master`
-   NEVER merge directly to `master` branch without a reviewed pull request. This insures all CI/CD testing and validation is in tact before
-   All pull request branches should begin with a Github issue reference number in the name and a dash-separated concise/general summary of the issue
    -   For example, an issue called "Setup Initial Django App to manage server #8" would have the following branch name: `8_setup-django`
    -   This helps ensure that all issues are accounted for and can be identified for future reference
-   If a task stretches beyond multiple Github issues, try to use feature flags to hide any dependent functionality.

### 1.2. Commits
-   All commit messages' first line should always follow a similar syntax:
    -   `(#[Issue Reference Number]) [ACTION TYPE]: [simple summary]`
    -   For example: `"(#7) DOC: Adding CI badges to README"`
    -   ***Action Types:***
        -   *`CONFIG`*: Generally used for tinkering with config files, dependency versioning, build-related code changes
        -   *`SETUP`*: Generally used for beginning work that will be enabling a future feature, such as bootstrapping the application framework with some starter code or adding empty directories/files in places where code will be
        -   *`INIT`*: Generally used for taking a first step at something that is not finished. This can be used interchangeably with *SETUP* for most use cases
        -   *`FEAT`*: Generally used to track features or atomic code improvements that introduce new functionality
        -   *`CLEAN`*: Generally used to track when dead code is removed or when making stylistic changes to code that does not change it's functionality such as improving the formatting to better match a style guide.
        -   *`FIX`*: Generally used to track bugs and resolving errors
        -   *`PATCH`*: Generally used to track temporary hotfixes to an urgent issue that will soon be replaced with a `FIX`
        -   *`DOC`*: Generally used to track documentation improvements whether through readme/markdown docs or through inline code documentation such as doc-strings and comments
        -   *`TEST`*: Generally used for adding/fixing tests and increasing coverage


### 1.3. Pull Requests
-   Pull requests should have a title that begins with `(#[Issue Reference Number])` such as:  `"(#8) setup django config"`
-   The description of the Pull request can use Github message triggers to indicate an action to be taken on the issue upon merging the Pull Request, such as `"Closes #8"`
-   All PR's must wait for builds to pass and should have no additional static analysis failures
-   When at all possible, please try to make sure any new code or fixed bugs have proper tests added as well when applicable.


## 2. Code Styling

### 2.1 Python
-   For all Python code (mainly **.py* files), we will be by default following [PEP8](https://www.python.org/dev/peps/pep-0008/) standards.
    -   We make one exception: a 120 character max line length instead of 80
-   For all application framework, by default we follow guidelines defined by [django's style guide](https://docs.djangoproject.com/en/2.2/internals/contributing/writing-code/coding-style/)
-   All files, classes, functions and methods should have  [Google-style docstrings](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) with the exception on tests unless necessary for understanding
-   All docstrings in functions and methods should have [type hinting](https://mypy.readthedocs.io/en/latest/cheat_sheet_py3.html) in the `Args` and `Returns` sections.
-   Lastly, we currently deploy this application using Python 3.7, but please make sure the code is compatible from Python 3.6-3.8+

### 2.2 JavaScript
-   For JavaScript, we strongly avoid injecting inline of HTML files and prefer all code be imported from .js files
-   We follow [ESLint](https://eslint.org/) guidelines for code styling.

### 2.3 HTML Templating
-   We leverage django templating wherever applicable in this project

## 3. Contact
If you get stuck or have any questions, feel free to reach out to the team/open a Github issue/or email kenneth@seals-nutt.com for more information.
