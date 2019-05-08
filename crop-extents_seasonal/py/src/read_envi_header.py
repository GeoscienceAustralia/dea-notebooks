import builtins
import numpy as np
def read_envi_header(file):
    '''
    USAGE: hdr = read_envi_header(file)
    Reads an ENVI ".hdr" file header and returns the parameters in a
    dictionary as strings.  Header field names are treated as case
    insensitive and all keys in the dictionary are lowercase.
    '''
    import warnings
    from spectral import settings
    f = builtins.open(file, 'r')

    try:
        starts_with_ENVI = f.readline().strip().startswith('ENVI')
    except UnicodeDecodeError:
        msg = 'File does not appear to be an ENVI header (appears to be a ' \
          'binary file).'
        f.close()
        raise FileNotAnEnviHeader(msg)
    else:
        if not starts_with_ENVI:
            msg = 'File does not appear to be an ENVI header (missing "ENVI" \
              at beginning of first line).'
            f.close()
            raise FileNotAnEnviHeader(msg)

    lines = f.readlines()
    f.close()

    dict = {}
    have_nonlowercase_param = False
    support_nonlowercase_params = settings.envi_support_nonlowercase_params
    try:
        while lines:
            line = lines.pop(0)
            if line.find('=') == -1: continue
            if line[0] == ';': continue

            (key, sep, val) = line.partition('=')
            key = key.strip()
            if not key.islower():
                have_nonlowercase_param = True
                if not support_nonlowercase_params:
                    key = key.lower()
            val = val.strip()
            if val and val[0] == '{':
                str = val.strip()
                while str[-1] != '}':
                    line = lines.pop(0)
                    if line[0] == ';': continue

                    str += '\n' + line.strip()
                if key == 'description':
                    dict[key] = str.strip('{}').strip()
                else:
                    vals = str[1:-1].split(',')
                    for j in range(len(vals)):
                        vals[j] = vals[j].strip()
                    dict[key] = vals
            else:
                dict[key] = val

        if have_nonlowercase_param and not support_nonlowercase_params:
            msg = 'Parameters with non-lowercase names encountered ' \
                  'and converted to lowercase. To retain source file ' \
                  'parameter name capitalization, set ' \
                  'spectral.setttings.envi_support_nonlowercase_params to ' \
                  'True.'
            warnings.warn(msg)
            print('Header parameter names converted to lower case.')
        return dict
    except:
        raise EnviHeaderParsingError()