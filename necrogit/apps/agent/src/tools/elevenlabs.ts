import { withSpan } from '../telemetry/sentry.js';
import fs from 'node:fs';
import path from 'node:path';

export interface SeanceAudioResult {
  transcript: string;
  voiceId: string;
  audioPath?: string;
  audioBase64?: string;
  durationEstimateSeconds: number;
  engine: string;
}

export class ElevenLabsSeanceVoice {
  private apiKey: string | null;
  private voiceId: string;

  constructor() {
    this.apiKey = process.env.ELEVENLABS_API_KEY || null;
    this.voiceId = process.env.ELEVENLABS_VOICE_ID || '21m00Tcm4TlvDq8ikWAM'; // Rachel / Haunting
  }

  async synthesizeSeance(
    repoName: string,
    originalAuthor: string,
    deathYear: number,
    resurrectionSummary: string
  ): Promise<SeanceAudioResult> {
    const transcript = `Hark, traveller of the terminal. I am the ghost of ${repoName}, authored by ${originalAuthor} and abandoned to the digital crypt in the year ${deathYear}. For more than a decade, my dependencies bitrotted in silence. But today, the séance is complete. NecroGit and Gemma 2 have cleansed my AST. My code breathes once more.`;

    return withSpan(
      `elevenlabs-seance-${repoName}`,
      'voice.elevenlabs',
      async () => {
        if (!this.apiKey || process.env.SEANCE_SIMULATION_MODE === 'true') {
          console.log(`[ElevenLabs] Using spectral séance audio transcript for ${repoName} (offline simulation mode).`);
          return {
            transcript,
            voiceId: this.voiceId,
            durationEstimateSeconds: 14.5,
            engine: 'ElevenLabs Spectral Voice Engine (Simulated Audio Stream)',
          };
        }

        try {
          const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${this.voiceId}`, {
            method: 'POST',
            headers: {
              'xi-api-key': this.apiKey,
              'Content-Type': 'application/json',
              'Accept': 'audio/mpeg',
            },
            body: JSON.stringify({
              text: transcript,
              model_id: 'eleven_multilingual_v2',
              voice_settings: {
                stability: 0.35, // More emotional/spectral fluctuation
                similarity_boost: 0.85,
              },
            }),
            signal: AbortSignal.timeout(8000),
          });

          if (res.ok) {
            const buffer = Buffer.from(await res.arrayBuffer());
            const outputDir = path.resolve(process.cwd(), 'storage', 'seance_audio');
            if (!fs.existsSync(outputDir)) {
              fs.mkdirSync(outputDir, { recursive: true });
            }
            const audioPath = path.join(outputDir, `${repoName}_seance.mp3`);
            fs.writeFileSync(audioPath, buffer);

            return {
              transcript,
              voiceId: this.voiceId,
              audioPath,
              audioBase64: buffer.toString('base64').substring(0, 200) + '...',
              durationEstimateSeconds: 14.8,
              engine: 'ElevenLabs Live Text-to-Speech API',
            };
          }
        } catch (err: any) {
          console.warn('[ElevenLabs] Live audio synthesis failed, using transcript fallback:', err.message);
        }

        return {
          transcript,
          voiceId: this.voiceId,
          durationEstimateSeconds: 14.5,
          engine: 'ElevenLabs Spectral Voice Engine (Fallback Transcript)',
        };
      },
      { repoName }
    );
  }
}
