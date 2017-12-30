function varargout = pause(varargin)
    % Writes a [PAUSE] to stdout when executed to alert any listeners

    % Special wrapper to prevent the symbolic package from emitting a
    % stream of pause events while it waits for input.
    stack = dbstack;
    if ismember('readblock', {stack.name})
        [varargout{1:nargout}] = builtin('pause', varargin{:});
        return;
    end

    % Flush the output before calling pause
    builtin('disp', '[PAUSE]')
    [varargout{1:nargout}] = builtin('pause', varargin{:});
end
