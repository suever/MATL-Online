function matl_runner(flags, command, inputs, outfile)
    % Turn on diary
    if ~exist('outfile', 'var')
        outfile = 'defout';
    end

    % Remove any old diary files
    if exist(outfile, 'file')
        delete(outfile);
    end
    diary(outfile);

    % If any inputs are provided, go ahead and fill up the inputs queue
    if exist('inputs', 'var') && ~isempty(inputs)
        inputs = regexp(inputs, '\n', 'split');
        input('INIT', inputs{:});
    end

    % Go ahead and disable all warnings
    warning off %#ok

    try
        % Execute the command
        matl(flags, command)
    catch ME
        % Ensure that we cleanup everything in case of an error
        builtin('disp', ['[STDERR]', ME.message])
    end

    % Clean up necessary pieces
    cleanup();

    function cleanup()
        diary off;

        % Turn off all listeners for printing figures. Trick drawnow into
        % thinking that they are printing which will just do a normal
        % drawnow rather than trying to save
        figs = findall(0, 'type', 'figure');
        set(figs, 'UserData', 1)
        delete(figs)
    end
end
