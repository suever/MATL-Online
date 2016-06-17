function result = input(prompt, varargin)

    persistent values

    mlock();

    if exist('prompt', 'var') && strcmp(prompt, 'INIT')
        values = varargin;
        result = [];
        return;
    end

    if isempty(values) || ~iscell(values)
        error('Unable to fetch user input');
        munlock
    end

    result = values{1};

    % Pop this from the top of the input stack
    values(1) = [];
end
