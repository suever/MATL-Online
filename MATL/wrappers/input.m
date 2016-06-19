function result = input(prompt, varargin)

    persistent values

    if exist('prompt', 'var')
        switch lower(prompt)
            case 'init'
                values = varargin;
                result = [];
                return;
            case 'clear'
                % Clear out all stored variables
                values = [];
                return;
        end
    end

    if isempty(values) || ~iscell(values)
        error('Unable to fetch user input');
    end

    result = values{1};

    % Pop this from the top of the input stack
    values(1) = [];
end
