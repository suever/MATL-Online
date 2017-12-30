function result = input(prompt, varargin)
    % input - Overloads the built-in input to provide input when requested
    %
    %   We "fill up" the queue with the provided inputs and then whenever
    %   the code calls INPUT, we provide them the item that's on the top of
    %   the stack. If no items exist, we throw an error rather than
    %   prompting the user. This allows us to prevent an interactive
    %   session.
    %
    % - Filling the Queue
    %
    %   Inputs arguments are placed into the queue by specifying 'init' as
    %   the first input parameter, and the other inputs are all other
    %   inputs.
    %
    %       input('init', 'input1', 'input2', 'input3')
    %
    % - Clearing the Queue
    %
    %   This function uses persistent variables so if you want to clear the
    %   input arguments for any reason you need to explicitly clear the
    %   queue out. To do this, you just pass 'clear' as the only input
    %
    %       input('clear')

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
