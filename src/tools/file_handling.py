import os
from debug_tools import p_i, p_in, p_line, p_e


def get_files(folder):
    file_list = os.listdir(folder)
    all_files = []
    for file in file_list:
        full_path = os.path.join(folder, file)
        if os.path.isdir(full_path):
            all_files = all_files + get_files(full_path)
        else:
            all_files.append(full_path)
    return all_files


def select_file(folder):
    files_in_folder = sorted(get_files(folder))
    info_text = []
    for i in range(len(files_in_folder)):
        file = files_in_folder[i].split('/')[-1]
        info_text.append('%i: %s' % (i + 1, file))
    p_i("Select one of these files to continue:")
    p_line(info_text)
    while True:
        try:
            selected_file = p_in("Select file: ")
            selected_file = int(selected_file)
        except ValueError:
            p_e('No valid file chosen.')
            continue
        if selected_file < 1 or selected_file > len(info_text):
            p_e('No valid file chosen.')
            continue
        file = files_in_folder[selected_file - 1]
        p_i('%s was selected' % file.split('/')[-1])
        break
    return file
