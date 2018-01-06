function varargout = audiowrite(varargin)
    % audiowrite - Intercepts audiowrite calls and forces format and path

    % The filename is input #1. We want to replace this with the filename
    % that we actually want/need.
    filename = generateUniqueFilename(pwd, 'audio', '.wav');
    builtin('disp', ['[AUDIO]', filename])

    [varargout{1:nargout}] = builtin('audiowrite', filename, varargin{2:end});
end
