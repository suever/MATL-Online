function varargout = drawnow(varargin)

    if get(gcf(), 'UserData')
        [varargout{1:nargout}] = builtin('drawnow', varargin{:});
    else
        set(gcf(), 'UserData', 1)

        base = 'image';

        fname = @(x)[base, num2str(x), '.png'];

        k = 0;
        while exist(fname(k), 'file')
            k = k + 1;
        end

        filename = fname(k);
        builtin('disp', (['[IMAGE]', fullfile(pwd, filename)]))
        print(gcf(), filename, '-dpng', '-tight')

        set(gcf(), 'UserData', 0)
    end
end
