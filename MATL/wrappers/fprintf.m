function varargout = fprintf(varargin)
    [varargout{1:nargout}] = builtin('fprintf', varargin{:});
end
