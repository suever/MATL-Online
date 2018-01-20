function fprintf(fid, varargin)
    % fprintf - Custom version of fprintf to properly handle stdout/stderr
    %
    %   In the online version, we want to ensure that we treat STDOUT and
    %   STDERR properly so that they can be parsed correctly by the
    %   front-end.

    switch fid
        case 1
            builtin('disp', ['[STDOUT]', sprintf(varargin{:})]);
        case 2
            builtin('disp', ['[STDERR]', sprintf(varargin{:})]);
        otherwise
            builtin('fprintf', fid, varargin{:});
    end
end
