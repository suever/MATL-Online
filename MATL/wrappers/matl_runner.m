function matl_runner(flags, command, varargin)
    % matl_runner - Wrapper function for dealing with MATL gracefully
    %
    %   We have to wrap calls to MATL for two primary reasons:
    %
    %       1. Passing input arguments
    %       2. Catching and returning useful error messages
    %
    %   This function serves both of these functions and allows us to use
    %   the MATL source directly without any modification.

    % If any inputs are provided, go ahead and fill up the inputs queue
    input('INIT', varargin{:});

    % Go ahead and disable all warnings
    warning off %#ok

    % Create a multi-line string if necessary
    if iscell(command)
        command = strjoin(command, '\n');
    end

    try
        % Execute the command
        matl(flags, command)
    catch ME
        % Ensure that we cleanup everything in case of an error
        pieces = regexp(ME.message, '\n', 'split');
        for k = 1:numel(pieces)
            if ~isempty(strtrim(pieces{k}))
                builtin('disp', ['[STDERR]', pieces{k}])
            end
        end
    end

    % Clean up necessary pieces
    cleanup();

    function cleanup()
        % Flush all inputs so they don't stick around to the next run
        input('clear');

        % Turn off all listeners for printing figures. Trick drawnow into
        % thinking that they are printing which will just do a normal
        % drawnow rather than trying to save
        figs = findall(0, 'type', 'figure');
        set(figs, 'UserData', 1)
        delete(figs)
    end
end
