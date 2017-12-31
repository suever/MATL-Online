function varargout = imwrite(varargin)
    % imwrite - Intercepts imwrite calls and forces format and location

    % If the second input is a colormap
    if numel(varargin) >= 2 && ~ischar(varargin{2})
        filename_ind = 3;
    else
        filename_ind = 2;
    end

    % Filename is going to be input #2. We want to replace this with the
    % filename that we actually want
    varargin{filename_ind} = generateUniqueFilename(pwd, 'image', '.png');
    builtin('disp', ['[IMAGE_NN]', varargin{filename_ind}])
    [varargout{1:nargout}] = builtin('imwrite', varargin{:});
end
