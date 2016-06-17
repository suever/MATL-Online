function varargout = drawnow(varargin)
    [varargout{1:nargout}] = builtin('drawnow', varargin{:});
end
