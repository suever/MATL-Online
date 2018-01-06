function sound(signal, sample_rate, varargin)
    % sound - Intercepts calls to sound and redirects them to audiowrite so
    %         that they generate an audio file that we can stream to the client

    if numel(varargin)
        params = {'BitsPerSample', varargin{1}}
    else
        params = {};
    end

    audiowrite('', signal, sample_rate, params{:});
end
