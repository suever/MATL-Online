function varargout = drawnow(varargin)
    % drawnow - Overloaded version of built-in
    %
    %   Whenever this function is executed, the graphics on the current
    %   figure are saved to images. This works because all plotting
    %   commands in MATL call a drawnow if output is expected at that
    %   point. This function just saves the images in the working directory
    %   to be colleceted later.

    % Get the current figure without creating a new one
    currentFigure = get(0, 'CurrentFigure');

    % If there are no figures or axes, carry on
    if isempty(currentFigure) || isempty(get(currentFigure, 'CurrentAxes'))
        builtin('drawnow');
        return;
    end

    if get(currentFigure, 'UserData')
        % If we're currently saving the figure, just let the internal
        % calls to drawnow just pass through to the built-in
        [varargout{1:nargout}] = builtin('drawnow', varargin{:});
    else
        % Set this so that we dont' try to re-print on every internal call
        % to drawnow
        set(currentFigure, 'UserData', 1)

        filename = generateUniqueFilename(pwd, 'image', '.png');
        builtin('disp', (['[IMAGE]', filename]))
        print(currentFigure, filename, '-dpng', '-r72');

        % Release this status so we're ready to print again if necessary
        set(currentFigure, 'UserData', 0)
    end
end
