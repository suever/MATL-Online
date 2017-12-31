function name = generateUniqueFilename(folder, prefix, extension)
    % Helper function for generating a unique filename

    % Anonymous function to generate the name. We keep them numbered
    % consecutively just in case we care at the other end
    generateName = @(x)fullfile(folder, [prefix, num2str(x), extension]);

    % Increment until we find an available name
    k = 0;
    while exist(generateName(k), 'file')
        k = k + 1;
    end

    name = generateName(k);
end
