function varargout = urlwrite(varargin)
    % urlwrite - Overloaded version of urlwrite to prevent web access

    error('access to URLs is disabled in MATL Online')
end
