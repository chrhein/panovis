import os
from tools.debug import p_i, p_in, p_line, p_e
from tkinter.filedialog import askopenfile, askopenfilenames
import tkinter as tk


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
    files_chosen = []
    while True:
        try:
            selected_file = p_in("Select file: ")
            selected_file = int(selected_file)
        except ValueError:
            try:
                x, y = selected_file.split('-')
                if min(int(x), int(y)) < 1 or max(int(x), int(y)) > len(info_text):
                    p_e('No valid file chosen.')
                    continue
                for i in range(min(int(x), int(y)), max(int(x)+1, int(y)+1)):
                    files_chosen.append(files_in_folder[i - 1])
                break
            except ValueError:
                p_e('No valid file chosen.')
            continue
        if selected_file < 1 or selected_file > len(info_text):
            p_e('No valid file chosen.')
            continue
        files_chosen.append(files_in_folder[selected_file - 1])
        break
    p_i('%s was selected' % str([i.split('/')[-1] for i in files_chosen]).strip('[]'))
    return files_chosen


def tui_select(it, itt='', in_t='', e_t='', afd=False):
    formatted_text = []
    for i in range(len(it)):
        formatted_text.append('%i: %s' % (i+1, it[i]))
    formatted_text.append('0: exit')
    p_line()
    p_i(itt)
    p_line(formatted_text)
    while True:
        try:
            mode = p_in(in_t)
            if mode == 'debug' and afd:
                return mode
            mode = int(mode)
        except ValueError:
            p_e(e_t)
            continue
        if mode == 0:
            exit()
        if mode < 1 or mode > len(it):
            p_e(e_t)
            continue
        return mode


def file_chooser(title, multiple=False):
    # Set environment variable
    os.environ['TK_SILENCE_DEPRECATION'] = '1'
    root = tk.Tk()
    root.withdraw()
    p_i('Opening File Explorer')
    if multiple:
        files = askopenfilenames(title=title,
                                 filetypes=[('PNGs', '*.png'),
                                            ('JPEGs', '*.jpeg'),
                                            ('JPGs', '*.jpg')])
    else:
        filename = askopenfile(title=title,
                               mode='r',
                               filetypes=[('PNGs', '*.png'),
                                          ('JPEGs', '*.jpeg'),
                                          ('JPGs', '*.jpg')])
    try:
        if multiple:
            p_i('%s was selected' % [i.split('/')[-1] for i in files])
            return files
        else:
            p_i('%s was selected' % filename.name.split('/')[-1])
            return filename.name
    except AttributeError:
        p_i('Exiting...')
        exit()
