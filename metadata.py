# -*- coding: utf-8 -*-
"""Project metadata
Information describing the project.
"""

# The package name, which is also the "UNIX name" for the project.
package = 'blueprints'
project = "Tachyonic Project " + package.title()
project_no_spaces = project.replace(' ', '')
# Please follow https://www.python.org/dev/peps/pep-0440/
version = '0.0.0'
description = project
author = 'Myria Solutions (PTY) Ltd'
email = 'project@tachyonic.org'
license = 'BSD3-Clause'
copyright = '2019 ' + author
url = 'http://www.tachyonic.org'
identity = project + ' v' + version
