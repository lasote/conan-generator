import os
import tempfile
from collections import defaultdict
from contextlib import contextmanager

BUILD_REQUIRE_SEPARATOR = "~>"
REQUIRE_SEPARATOR = "->"

@contextmanager
def chdir(newdir):
    old_path = os.getcwd()
    os.chdir(newdir)
    try:
        yield
    finally:
        os.chdir(old_path)


@contextmanager
def environment_append(env_vars):
    """
    :param env_vars: List of simple environment vars. {name: value, name2: value2} => e.g.: MYVAR=1
                     The values can also be lists of appendable environment vars. {name: [value, value2]}
                      => e.g. PATH=/path/1:/path/2
    :return: None
    """
    for name, value in env_vars.items():
        if isinstance(value, list):
            env_vars[name] = os.pathsep.join(value)
            old = os.environ.get(name)
            if old:
                env_vars[name] += os.pathsep + old
    if env_vars:
        old_env = dict(os.environ)
        os.environ.update(env_vars)
        try:
            yield
        finally:
            os.environ.clear()
            os.environ.update(old_env)
    else:
        yield

def get_full_ref(name):
    tmp = name.replace("@", "/").split("/")
    if len(tmp) == 1:
        return "%s/1.0@user/channel" % name
    elif len(tmp) == 2:
        return "%s@user/channel" % name
    else:
        return name

def get_only_name(name):
   return get_full_ref(name).replace("@", "/").split("/", 1)[0]

def get_only_version(name):
   return get_full_ref(name).replace("@", "/").split("/", 2)[1]


def get_conanfile(name, requires, build_requires):
    only_name = get_only_name(name)
    only_version = get_only_version(name)
    conanfile = """
from conans import ConanFile

class ConanLib(ConanFile):
    name = "{name}"
    version = "{version}"
""".format(name=only_name, version=only_version)
    if requires:
        conanfile += """
    requires = %s
""" % ", ".join(['"%s"' % get_full_ref(n) for n in requires])
    if build_requires:
        conanfile += """
    build_requires = %s
""" % ", ".join(['"%s"' % get_full_ref(n) for n in build_requires])

    return conanfile

def create(name, requires, build_requires, workdir):
    t = os.path.join(workdir, get_full_ref(name).replace("@", "_").replace("/", "_"))
    os.mkdir(t)
    with chdir(t):
        c = get_conanfile(name, requires, build_requires)
        with open("conanfile.py", "w") as f:
            f.write(c)
        ret = os.system("conan create . user/channel")
        if ret != 0:
            raise Exception("Error calling conan create")

def get_pending_nodes(requires, build_requires, visited):
    ret = []
    if requires:
        for r in requires:
            if r not in visited:
                ret.append(r)
    if build_requires:
        for r in build_requires:
            if r not in visited:
                ret.append(r)
    return ret

def process_node(node, requires, build_requires, visited, workdir):
    if node in visited:
        return
    pending = get_pending_nodes(requires.get(node), build_requires.get(node), visited)
    for p in pending:
        # Recursion
        process_node(p, requires, build_requires, visited, workdir)
    create(node, requires.get(node), build_requires.get(node), workdir)
    visited.append(node)


def process(path_file):

    requires = defaultdict(list)
    build_requires =  defaultdict(list)
    nodes = set()
    with open(path_file, "r") as f:
        contents = f.read()

    for line in contents.splitlines():
        if not line:
            continue
        for separator in (BUILD_REQUIRE_SEPARATOR, REQUIRE_SEPARATOR):
            if separator in line:
                n1, n2 = [c.strip() for c in line.split(separator)]
                nodes.add(n1)
                nodes.add(n2)
                if separator == REQUIRE_SEPARATOR:
                    requires[n1].append(n2)
                else:
                    build_requires[n1].append(n2)

    cache_dir = tempfile.mkdtemp()
    workdir = tempfile.mkdtemp()
    visited = []
    with environment_append({"CONAN_USER_HOME": cache_dir}):
        t = tempfile.mkdtemp()
        for node in nodes:
            process_node(node, requires, build_requires, visited, workdir)
    print("export CONAN_USER_HOME=%s && cd %s" % (cache_dir, workdir))

if __name__ == "__main__":
    process("nodes.conan")


