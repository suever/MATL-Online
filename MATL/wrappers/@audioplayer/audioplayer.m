classdef audioplayer < handle
    % audioplayer - Custom class to override default behavior of audioplayer
    %
    %   In the online interpreter, rather than playing audio via the audio
    %   device, we want to save the audio as an audio file. In this way, we
    %   redirect the output to AUDIOWRITE when calling PLAYBLOCKING on the
    %   AUDIOPLAYER object.

    properties (Access = 'private')
        data
        sample_rate
        bits
    end

    methods
        function self = audioplayer(data, sample_rate, bits)
            self.data = data;
            self.sample_rate = sample_rate;
            self.bits = bits;
        end

        function playblocking(self)
            audiowrite('', self.data, self.sample_rate, 'BitsPerSample', self.bits);
        end
    end
end
