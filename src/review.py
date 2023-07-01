import hashlib
import json
import os
import re
import subprocess


def __get_defines(path_source, depara):
    regex_list = [
        "#define .* .*",
        "#  define .* .*",
    ]

    for root, dirs, files in os.walk(path_source):
        for file in files:
            file_path = os.path.join(root, file)

            if '/test/' in file_path or 'moc_' in file_path:
                continue

            if file_path.endswith(".h"):
                defines = []

                with open(file_path, 'r') as arquivo:
                    for line in arquivo:
                        match = False

                        for regex in regex_list:
                            match = re.match(regex, line)

                            if match:
                                break

                        if match:
                            line = line.replace("#", "")
                            line = line.strip()
                            line = line[line.index(' ') + 1:]
                            line = line.strip()
                            line = line[0:line.index(' ')]
                            defines.append(line)

                if len(defines) > 0:
                    name_include = file_path[file_path.rindex('/') + 1:]
                    name_include = name_include[0:name_include.index('.')]

                    if name_include in depara:
                        defines.extend(depara[name_include])

                    depara[name_include] = defines


def __get_method_name(path_source, depara):
    for root, dirs, files in os.walk(path_source):
        for file in files:
            file_path = os.path.join(root, file)

            if '/test/' in file_path or 'moc_' in file_path:
                continue

            if file_path.endswith(".h"):
                data = subprocess.run(
                    'ctags --output-format=json --format=2 --fields=+line ' + file_path,
                    shell=True,
                    capture_output=True,
                    text=True,
                ).stdout

                for obj in data.split('\n'):
                    if obj == '':
                        continue

                    obj = json.loads(obj)

                    if not obj['_type'] == "tag":
                        continue

                    if not obj['kind'] == 'member':
                        continue

                    if not obj['scopeKind'] == 'class':
                        continue

                    name = obj['name']

                    if name.startswith("_"):
                        name = name[1:]

                    typeref = obj['typeref'].lower()

                    if 'qlist<' in typeref:
                        typeref = typeref[0:len(typeref) - 2]
                        typeref = typeref.replace("qlist<", "")

                    if not typeref.endswith(" *"):
                        continue

                    typeref = typeref[0:len(typeref) - 2]

                    if typeref.startswith("typename:"):
                        typeref = typeref.replace("typename:", "")

                    depara_de = [name + "()"]

                    if typeref in depara:
                        depara_de.extend(depara[typeref])

                    depara[typeref] = depara_de


def __get_constexpr(path_source, depara):
    regex_list = [
        "constexpr const char\* .* = \".*\";.*"
    ]

    for root, dirs, files in os.walk(path_source):
        for file in files:
            file_path = os.path.join(root, file)

            if '/test/' in file_path or 'moc_' in file_path:
                continue

            if file_path.endswith(".h"):
                defines = []

                with open(file_path, 'r') as arquivo:
                    for line in arquivo:
                        match = False

                        for regex in regex_list:
                            match = re.match(regex, line)

                            if match:
                                break

                        if match:
                            line = line.replace("constexpr const char* ", "")
                            line = line.strip()
                            line = line[0:line.index(' ')]
                            defines.append(line)

                if len(defines) > 0:
                    name_include = file_path[file_path.rindex('/') + 1:]
                    name_include = name_include[0:name_include.index('.')]

                    if name_include in depara:
                        defines.extend(depara[name_include])

                    depara[name_include] = defines


def __get_typedef(path_source, depara):
    regex_list = [
        "typedef int \(\* .*"
    ]

    for root, dirs, files in os.walk(path_source):
        for file in files:
            file_path = os.path.join(root, file)

            if '/test/' in file_path or 'moc_' in file_path:
                continue

            if file_path.endswith(".h"):
                defines = []

                with open(file_path, 'r') as arquivo:
                    for line in arquivo:
                        match = False

                        for regex in regex_list:
                            match = re.match(regex, line)

                            if match:
                                break

                        if match:
                            line = line.replace("typedef int (* ", "")
                            line = line.strip()
                            line = line[0:line.index(')')]
                            defines.append(line)

                if len(defines) > 0:
                    name_include = file_path[file_path.rindex('/') + 1:]
                    name_include = name_include[0:name_include.index('.')]

                    if name_include in depara:
                        defines.extend(depara[name_include])

                    depara[name_include] = defines


def review(config):
    depara = config['depara']
    suffix_get = config['suffixGet']
    ignore_path = config['ignorePath']
    path_source = config['path_source']

    for path_include in config['pathInclude']:
        __get_defines(path_include, depara)
        __get_constexpr(path_include, depara)
        __get_typedef(path_include, depara)
        __get_method_name(path_include, depara)

    comments = []
    path_size = len(path_source) + 1

    for root, dirs, files in os.walk(path_source):
        for file in files:
            file_path = os.path.join(root, file)

            if "/test/" in file_path or "/.moc/" in file_path:
                continue

            if not file_path.endswith(".cpp") and not file_path.endswith(".h"):
                continue

            includes_to_remove = []

            arquivo_original = []

            with open(file_path, 'r') as arquivo:
                includes = []
                conteudo = []
                in_file = file_path[path_size:]

                if __ignore_path(in_file, ignore_path):
                    continue

                for linha in arquivo:
                    arquivo_original.append(linha)
                    if linha.startswith("using "):
                        continue

                    if linha.startswith("#include "):
                        includes.append(linha)
                    else:
                        conteudo.append(linha)

                for name in includes:
                    original_name = name
                    name = __get_name(name)

                    if not __contains_include(depara, name, conteudo, suffix_get):
                        includes_to_remove.append(original_name)
                        comment = f'Include {name} nao utilizado no arquivo {in_file}'
                        comments.append({
                            "id": __generate_md5(comment),
                            "comment": comment,
                        })

            output_text = []

            if len(includes_to_remove) == 0:
                continue

            for linha in arquivo_original:
                remove_line = False

                for include in includes_to_remove:
                    if include == linha:
                        remove_line = True

                if not remove_line:
                    output_text.append(linha)

            output_text = ''.join(output_text)

            # with open(file_path, "w") as arquivo:
            #    arquivo.write(output_text)

    return comments


def __get_name(name):
    name = name.replace(".h>", "")
    name = name.replace(".h\"", "")
    name = name.replace(".cpp>", "")
    name = name.replace(".cpp\"", "")
    name = name.replace(">", "")
    name = name.replace("\n", "")
    name = name.lower()

    if '/' in name:
        name = name[name.rfind('/') + 1:]
    elif '"' in name:
        name = name[name.rfind('"') + 1:]
    else:
        name = name[name.rfind('<') + 1:]

    return name


def __contains_include(depara_obj, name, conteudo, suffix_get):
    names = [name]

    if name in depara_obj:
        for depara in depara_obj[name]:
            names.append(depara.lower())

    if name.startswith("ui_"):
        names.append("ui->")
        names.append("ui(")

    if name.endswith(suffix_get):
        name_without_suffix_get = name[0:len(name) - len(suffix_get)]

        names.append(f"get{name_without_suffix_get}()->")
        names.append(f"{name_without_suffix_get}()->")
        names.append(f"get{name}()->")
        names.append(f"{name}()->")
        names.append(f"{name_without_suffix_get}->")
        names.append(f"{name}->")
        names.append(f"get{name_without_suffix_get}().")
        names.append(f"{name_without_suffix_get}().")
        names.append(f"get{name}().")
        names.append(f"{name}().")
        names.append(f"{name_without_suffix_get}.")
        names.append(f"{name}.")

    for linha in conteudo:
        for depara in names:
            if depara in linha.lower():
                return True

    return False


def __ignore_path(path, ignore_path):
    for ignore in ignore_path:
        if path.startswith(ignore):
            return True

    return False


def __generate_md5(string):
    md5_hash = hashlib.md5()
    md5_hash.update(string.encode('utf-8'))
    return md5_hash.hexdigest()
