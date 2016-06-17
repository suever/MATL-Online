function matl_runner(flags, command, inputs, outfile)
    % Turn on diary
    if ~exist('outfile', 'var')
        outfile = 'defout';
    end

    % Remove any old diary files
    delete(outfile);
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
        cleanup();
        rethrow(ME);
    end

    % Clean up necessary pieces
    cleanup();

    function cleanup()
        diary off;
    end
end
