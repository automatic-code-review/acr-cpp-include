import hashlib
import os


def review(config):
    depara = config['depara']
    suffix_get = config['suffixGet']
    ignore_path = config['ignorePath']
    path_source = config['path_source']

    comments = []
    path_size = len(path_source) + 1

    for root, dirs, files in os.walk(path_source):
        for file in files:
            file_path = os.path.join(root, file)

            if not file_path.endswith(".cpp") and not file_path.endswith(".h"):
                continue

            with open(file_path, 'r') as arquivo:
                includes = []
                conteudo = []
                in_file = file_path[path_size:]

                if __ignore_path(in_file, ignore_path):
                    continue

                for linha in arquivo:
                    if linha.startswith("using "):
                        continue

                    if linha.startswith("#include "):
                        includes.append(linha)
                    else:
                        conteudo.append(linha)

                for name in includes:
                    name = __get_name(name)

                    if not __contains_include(depara, name, conteudo, suffix_get):
                        comment = f'Include {name} nao utilizado no arquivo {in_file}'
                        comments.append({
                            "id": __generate_md5(comment),
                            "comment": comment,
                        })

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

    if name.endswith(suffix_get):
        name_without_suffix_get = name[0:len(name) - len(suffix_get)]

        names.append(f"get{name_without_suffix_get}()->")
        names.append(f"{name_without_suffix_get}()->")
        names.append(f"get{name}()->")
        names.append(f"{name}()->")
        names.append(f"{name_without_suffix_get}->")
        names.append(f"{name}->")

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
