import json
import os
import re

if __name__ == '__main__':
    regex_list = [
        "#define .* .*",
        "#  define .* .*"
    ]
    depara = {

    }

    for root, dirs, files in os.walk(
            "TODO"
    ):
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
                    depara[name_include] = defines

    with open("arquivo.json", 'w') as json_file:
        json.dump(depara, json_file, indent=True)
