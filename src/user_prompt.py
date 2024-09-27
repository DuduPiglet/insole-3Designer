import conf.strings as text

def prompt_inputfile(files, lang='en'):
    selection = None
    while (selection == None):
        for ix, file in enumerate(files):
            print("  %d - %s" % (ix, file))
        try:
            selection = int(input(text.texts['prompt_inputfile'][lang]))
        except ValueError:
            selection = None
            print("\n%s" % text.texts['warn_bad_inputfile'][lang])
            continue
        if (selection > ix):
            selection = None
            print("\n%s" % text.texts['warn_bad_inputfile'][lang])
            continue
    print(text.texts['selection_inputfile'][lang] % files[selection])
    print("")
    return files[selection]

def prompt_footlength(lang='en'):
    footlength = None
    while (footlength == None):
        try:
            footlength = int(input(text.texts['prompt_footlength'][lang]))
        except ValueError:
            footlength = None
            print("\n%s" % text.texts['warn_bad_footlength'][lang])
            continue
        if ((footlength < 200) or (footlength > 400)):
            footlength = None
            print("\n%s" % text.texts['warn_bad_footlength'][lang])
            continue
    print('')
    return footlength

def prompt_footlength_ml(lang='en'):
    meshlab_footlength = None
    while (meshlab_footlength == None):
        try:
            meshlab_footlength = float(input(text.texts['prompt_meshlabfootlength'][lang]))
        except ValueError:
            meshlab_footlength = None
            print("\n%s" % text.texts['warn_bad_meshlabfootlength'][lang])
            continue
        if ((meshlab_footlength < 1) or (meshlab_footlength > 20)):
            meshlab_footlength = None
            print("\n%s" % text.texts['warn_bad_meshlabfootlength'][lang])
            continue
    print('')
    return meshlab_footlength

def prompt_foot_choise(lang='en'):
    foot_choise = None
    while (foot_choise == None):
        try:
            foot_choise = input(text.texts['prompt_foot_choise'][lang])
        except ValueError:
            foot_choise = None
            print("\n%s" % text.texts['warn_bad_foot_choise'][lang])
            continue
        if ((lang == 'en') and (foot_choise != 'l') and (foot_choise != 'r')):
            foot_choise = None
            print("\n%s" % text.texts['warn_bad_foot_choise'][lang])
            continue
        if ((lang == 'es') and (foot_choise != 'i') and (foot_choise != 'd')):
            foot_choise = None
            print("\n%s" % text.texts['warn_bad_foot_choise'][lang])
            continue
    if (lang == 'es'):
        if (foot_choise == 'i'):
            foot_choise = 'l'
        elif (foot_choise == 'd'):
            foot_choise = 'r'
    print('')
    return foot_choise

def prompt_outputfile_name(lang='en', default_output_filename='output.stl'):
    output_file_name = None
    while (output_file_name == None):
        try:
            output_file_name = input(text.texts['prompt_output_file_name'][lang] % default_output_filename)
        except ValueError:
            output_file_name = None
            print("\n%s" % text.texts['warn_bar_output_file_name'][lang])
            continue
        if (output_file_name == ""):
            print('')
            return default_output_filename
        output_file_name_split = output_file_name.split('.')
        if (len(output_file_name_split) > 1):
            if (output_file_name_split[-1] == "stl"):
                print('')
                return output_file_name
        print('')
        return ("%s.stl" % output_file_name)

if __name__ == '__main__':
  print("This is a helper module for the insole-3Designer app.")