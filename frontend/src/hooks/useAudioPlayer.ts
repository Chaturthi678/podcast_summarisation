import { useState, useRef, useCallback, useEffect } from 'react';

export interface AudioPlayerState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  playbackRate: number;
  error: string | null;
}

export function useAudioPlayer(src: string | null) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [state, setState] = useState<AudioPlayerState>({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    volume: 1,
    playbackRate: 1,
    error: null,
  });

  // Setup audio element
  useEffect(() => {
    if (!src) return;
    const audio = new Audio(src);
    audioRef.current = audio;

    audio.addEventListener('timeupdate', () => {
      setState(s => ({ ...s, currentTime: audio.currentTime }));
    });
    audio.addEventListener('loadedmetadata', () => {
      setState(s => ({ ...s, duration: Number.isFinite(audio.duration) ? audio.duration : 0, error: null }));
    });
    audio.addEventListener('error', () => {
      setState(s => ({ ...s, isPlaying: false, error: 'This audio file could not be played.' }));
    });
    audio.addEventListener('ended', () => {
      setState(s => ({ ...s, isPlaying: false }));
    });
    audio.addEventListener('play', () => setState(s => ({ ...s, isPlaying: true })));
    audio.addEventListener('pause', () => setState(s => ({ ...s, isPlaying: false })));

    return () => {
      audio.pause();
      audio.src = '';
    };
  }, [src]);

  const play = useCallback(() => audioRef.current?.play(), []);
  const pause = useCallback(() => audioRef.current?.pause(), []);

  const togglePlay = useCallback(() => {
    if (!audioRef.current) return;
    if (audioRef.current.paused) audioRef.current.play().catch(() => {
      setState(s => ({ ...s, isPlaying: false, error: 'Playback could not start. Check the audio file and try again.' }));
    });
    else audioRef.current.pause();
  }, []);

  const seekTo = useCallback((time: number) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = time;
  }, []);

  const setVolume = useCallback((vol: number) => {
    if (!audioRef.current) return;
    audioRef.current.volume = vol;
    setState(s => ({ ...s, volume: vol }));
  }, []);

  const setRate = useCallback((rate: number) => {
    if (!audioRef.current) return;
    audioRef.current.playbackRate = rate;
    setState(s => ({ ...s, playbackRate: rate }));
  }, []);

  return { state, play, pause, togglePlay, seekTo, setVolume, setRate };
}
