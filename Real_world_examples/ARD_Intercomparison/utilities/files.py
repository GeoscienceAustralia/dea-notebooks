"""
Provides utilities dealing with files.
"""

import os
import sys
import logging
import datetime
import numpy as np
from time import ctime, localtime, strftime

try:
    import hashlib
    md5_constructor = hashlib.md5
except ImportError:
    import md5
    md5_constructor = md5.new

__version__ = '$Id: files.py 685 2012-03-29 04:22:32Z carthur $'

logger = logging.getLogger()

if not getattr(__builtins__, "WindowsError", None):
    class WindowsError(OSError):
        pass


def fl_module_path(level=1):
    """
    Get the path of the module <level> levels above this function

    :param int level: level in the stack of the module calling this function
                      (default = 1, function calling ``fl_module_path``)

    :returns: path, basename and extension of the file containing the module

    :Example: path, base, ext = fl_module_path( ), Calling fl_module_path()
              from "/foo/bar/baz.py" produces the result "/foo/bar", "baz",
              ".py"
    """

    filename = os.path.realpath(sys._getframe(level).f_code.co_filename)
    path, fname = os.path.split(filename)
    base, ext = os.path.splitext(fname)
    path = path.replace(os.path.sep, '/')
    return path, base, ext


def fl_module_name(level=1):
    """
    Get the name of the module <level> levels above this function

    :param int level: Level in the stack of the module calling this function
                      (default = 1, function calling ``fl_module_name``)

    :returns: Module name.
    :rtype: str

    :Example: mymodule = fl_module_name( ) Calling fl_module_name() from
              "/foo/bar/baz.py" returns "baz"

    """

    package = sys._getframe(level).f_code.co_name
    return package


def fl_program_version(level=None):
    """
    Return the __version__ string from the top-level program, where defined.

    If it is not defined, return an empty string.

    :param int level: level in the stack of the main script
                      (default = maximum level in the stack)

    :returns: version string (defined as the ``__version__`` global variable)

    """

    if not level:
        import inspect
        level = len(inspect.stack()) - 1
    f = sys._getframe(level)
    if '__version__' in f.f_globals:
        return f.f_globals['__version__']
    else:
        return ''


def fl_load_file(filename, comments='%', delimiter=',', skiprows=0):
    """
    Load a delimited text file -- uses :func:`numpy.genfromtxt`

    :param filename: File, filename, or generator to read
    :type  filename: file or str
    :param comments: (default '%') indicator
    :type  comments: str, optional
    :param delimiter: The string used to separate values.
    :type  delimiter: str, int or sequence, optional

    """

    return np.genfromtxt(filename, comments=comments, delimiter=delimiter,
                         skip_header=skiprows)


def fl_save_file(filename, data, header='', delimiter=',', fmt='%.18e'):
    """
    Save data to a file.

    Does some basic checks to ensure the path exists before attempting
    to write the file. Uses :class:`numpy.savetxt` to save the data.

    :param str filename: Path to the destination file.
    :param data: Array data to be written to file.
    :param str header: Column headers (optional).
    :param str delimiter: Field delimiter (default ',').
    :param str fmt: Format statement for writing the data.

    """

    directory, fname = os.path.split(filename)
    if not os.path.isdir(directory):
        os.makedirs(directory)

    try:
        np.savetxt(filename, data, header=header, delimiter=delimiter,
                   fmt=fmt, comments='%')
    except TypeError:
        np.savetxt(filename, data, delimiter=delimiter, fmt=fmt, comments='%')


def fl_get_stat(filename, chunk_whole=2 ** 16):
    """
    Get basic statistics of filename - namely directory, name (excluding
    base path), md5sum and the last modified date. Useful for checking
    if a file has previously been processed.

    :param str filename: Filename to check.
    :param int chunk_whole: (optional) chunk size (for md5sum calculation).

    :returns: path, name, md5sum, modification date for the file.
    :raises TypeError: if the input file is not a string.
    :raises IOError: if the file is not a valid file, or if the file
                     cannot be opened.

    :Example: dir, name, md5sum, moddate = fl_get_stat(filename)

    """

    try:
        fh = open(filename)
        fh.close()
    except:
        logger.exception("Cannot open %s" % (filename))
        raise IOError("Cannot open %s" % (filename))

    try:
        directory, fname = os.path.split(filename)
    except:
        logger.exception('Input file is not a string')
        raise TypeError('Input file is not a string')

    try:
        si = os.stat(filename)
    except IOError:
        logger.exception('Input file is not a valid file: %s' % (filename))
        raise IOError('Input file is not a valid file: %s' % (filename))

    moddate = ctime(si.st_mtime)
    m = md5_constructor()
    f = open(filename, 'rb')

    while True:
        chunk = f.read(chunk_whole)
        if not chunk:
            break
        m.update(chunk)
    md5sum = m.hexdigest()

    return directory, fname, md5sum, moddate


def fl_config_file(extension='.ini', prefix='', level=None):
    """
    Build a configuration filename (default extension .ini) based on the
    name and path of the function/module calling this function. Can also
    be useful for setting log file names automatically.
    If prefix is passed, this is preprended to the filename.

    :param str extension: file extension to use (default '.ini'). The
                          period ('.') must be included.
    :param str prefix: Optional prefix to the filename (default '').
    :param level: Optional level in the stack of the main script
                  (default = maximum level in the stack).

    :returns: Full path of calling function/module, with the source file's
              extension replaced with extension, and optionally prefix
              inserted after the last path separator.

    :Example: configFile = fl_config_file('.ini') Calling fl_config_file from
              /foo/bar/baz.py should return /foo/bar/baz.ini
    """

    if not level:
        import inspect
        level = len(inspect.stack())

    path, base, ext = fl_module_path(level)
    config_file = os.path.join(path, prefix + base + extension)
    config_file = config_file.replace(os.path.sep, '/')
    return config_file


def fl_start_log(log_file, log_level, verbose=False, datestamp=False,
                 newlog=True):
    """
    Start logging to log_file all messages of log_level and higher.
    Setting ``verbose=True`` will report all messages to STDOUT as well.

    :param str log_file: Full path to log file.
    :param str log_level: String specifiying one of the standard Python logging
                         levels ('NOTSET','DEBUG','INFO','WARNING','ERROR',
                         'CRITICAL')
    :param boolean verbose: ``True`` will echo all logging calls to STDOUT
    :param boolean datestamp: ``True`` will include a timestamp of the creation
                              time in the filename.
    :param boolean newlog: ``True`` will create a new log file each time this
                           function is called. ``False`` will append to the
                           existing file.

    :returns: :class:`logging.logger` object.

    :Example: fl_start_log('/home/user/log/app.log', 'INFO', verbose=True)

    """

    if datestamp:
        b, e = os.path.splitext(log_file)
        curdate = datetime.datetime.now()
        curdatestr = curdate.strftime('%Y%m%d%H%M')
        # The lstrip on the extension is required as splitext leaves it on.
        log_file = "%s.%s.%s" % (b, curdatestr, e.lstrip('.'))

    log_dir = os.path.dirname(os.path.realpath(log_file))
    if not os.path.isdir(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError:
            # Unable to create the directory, so stick it in the
            # current working directory:
            path, fname = os.path.split(log_file)
            log_file = os.path.join(os.getcwd(), fname)

    if newlog:
        mode = 'w'
    else:
        mode = 'a'

    logging.basicConfig(level=getattr(logging, log_level),
                        format='%(asctime)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=log_file,
                        filemode=mode)
    logger = logging.getLogger()

    if len(logger.handlers) < 2:
        # Assume that the second handler is a StreamHandler for verbose
        # logging. This ensures we do not create multiple StreamHandler
        # instances that will *each* print to STDOUT
        if verbose and sys.stdout.isatty():
            # If set to true, all logging calls will also be printed to the
            # console (i.e. STDOUT)
            console = logging.StreamHandler()
            console.setLevel(getattr(logging, log_level))
            formatter = logging.Formatter('%(asctime)s: %(message)s',
                                          '%H:%M:%S', )
            console.setFormatter(formatter)
            logger.addHandler(console)

    logger.info('Started log file %s (detail level %s)' %
                (log_file, log_level))
    logger.info('Running %s (pid %d)' % (sys.argv[0], os.getpid()))
    logger.info('Version %s' % (fl_program_version()))
    return logger


def fl_log_fatal_error(tblines):
    """
    Log the error messages normally reported in a traceback so that
    all error messages can be caught, then exit. The input 'tblines'
    is created by calling ``traceback.format_exc().splitlines()``.

    :param list tblines: List of lines from the traceback.

    """

    for line in tblines:
        logger.critical(line.lstrip())
    sys.exit()


def fl_mod_date(filename, dateformat='%Y-%m-%d %H:%M:%S'):
    """
    Return the last modified date of the input file

    :param str filename: file name (full path).
    :param str dateformat: Format string for the date (default
                           '%Y-%m-%d %H:%M:%S')

    :returns: File modification date/time as a string
    :rtype: str

    :Example: modDate = fl_mod_date( 'C:/foo/bar.csv' ,
                                 dateformat='%Y-%m-%dT%H:%M:%S' )
    """

    try:
        si = os.stat(filename)
    except IOError:
        logger.exception('Input file is not a valid file: %s' % (filename))
        raise IOError('Input file is not a valid file: %s' % (filename))
    moddate = localtime(si.st_mtime)

    return strftime(dateformat, moddate)


def fl_size(filename):
    """
    Return the size of the input file in bytes

    :param str filename: Full path to the file.

    :returns: File size in bytes.
    :rtype: int

    :Example: file_size = fl_size( 'C:/foo/bar.csv' )
    """

    try:
        si = os.stat(filename)
    except WindowsError:
        logger.exception('Input file is not a valid file: %s' % (filename))
        raise IOError('Input file is not a valid file: %s' % (filename))
    except IOError:
        logger.exception('Input file is not a valid file: %s' % (filename))
        raise IOError('Input file is not a valid file: %s' % (filename))
    else:
        size = si.st_size

    return size


