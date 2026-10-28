import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { withSpan } from '../telemetry/sentry.js';

export interface BitrotAuditResult {
  repo_name: string;
  language: string;
  days_inactive: number;
  bitrot_risk_class: 'Critical' | 'High' | 'Medium' | 'Low';
  confidence_probabilities: Record<string, number>;
  cve_vulnerability_risk: number;
  bitrot_index: number;
  exorcism_complexity: string;
  zombie_dependencies_detected: number;
  engine: string;
  time_of_death?: {
    estimated_death_year: number;
    years_in_crypt: number;
    ghost_status: string;
    resurrection_urgency: string;
  };
}

export class TabPfnClient {
  private pythonPath: string;
  private serverScript: string;
  private benchmarkPath: string;

  constructor() {
    this.pythonPath = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
    
    // Locate server.py
    const candidates = [
      path.resolve(process.cwd(), 'services', 'tabpfn-service', 'server.py'),
      path.resolve(process.cwd(), '..', '..', 'services', 'tabpfn-service', 'server.py'),
      path.resolve(__dirname, '..', '..', '..', '..', 'services', 'tabpfn-service', 'server.py'),
    ];
    this.serverScript = candidates.find(c => fs.existsSync(c)) || candidates[0];

    // Locate benchmark data
    const benchCandidates = [
      path.resolve(process.cwd(), 'services', 'tabpfn-service', 'data', 'graveyard_benchmark.csv'),
      path.resolve(process.cwd(), '..', '..', 'services', 'tabpfn-service', 'data', 'graveyard_benchmark.csv'),
      path.resolve(__dirname, '..', '..', '..', '..', 'services', 'tabpfn-service', 'data', 'graveyard_benchmark.csv'),
    ];
    this.benchmarkPath = benchCandidates.find(c => fs.existsSync(c)) || '';
  }

  async auditBitrot(
    repoName: string,
    language: string,
    daysInactive: number,
    dependencyCount: number,
    unpinnedRatio: number,
    cyclomaticEntropy: number
  ): Promise<BitrotAuditResult> {
    return withSpan(
      `tabpfn-audit-${repoName}`,
      'ml.forensics',
      async () => {
        return new Promise<BitrotAuditResult>((resolve, reject) => {
          const args = [
            this.serverScript,
            '--audit',
            '--repo', repoName,
            '--lang', language,
            '--days', String(daysInactive),
            '--deps', String(dependencyCount),
            '--unpinned', String(unpinnedRatio),
            '--entropy', String(cyclomaticEntropy),
          ];

          if (this.benchmarkPath) {
            args.push('--benchmark', this.benchmarkPath);
          }

          const child = spawn(this.pythonPath, args, { stdio: ['ignore', 'pipe', 'pipe'] });
          let stdout = '';
          let stderr = '';

          child.stdout.on('data', d => { stdout += d.toString(); });
          child.stderr.on('data', d => { stderr += d.toString(); });

          child.on('close', code => {
            if (code !== 0) {
              console.warn(`[TabPFN] Subprocess exited with code ${code}, falling back to analytical estimate. Details: ${stderr}`);
              return resolve(this.fallbackAudit(repoName, language, daysInactive, dependencyCount, unpinnedRatio, cyclomaticEntropy));
            }
            try {
              const jsonMatch = stdout.match(/\{[\s\S]*\}/);
              if (!jsonMatch) {
                throw new Error('No JSON payload found in stdout');
              }
              const parsed = JSON.parse(jsonMatch[0]);
              resolve(parsed);
            } catch (err: any) {
              console.warn('[TabPFN] JSON parse failure, using fallback:', err.message);
              resolve(this.fallbackAudit(repoName, language, daysInactive, dependencyCount, unpinnedRatio, cyclomaticEntropy));
            }
          });

          child.on('error', err => {
            console.warn('[TabPFN] Failed to spawn python:', err.message);
            resolve(this.fallbackAudit(repoName, language, daysInactive, dependencyCount, unpinnedRatio, cyclomaticEntropy));
          });
        });
      },
      { repoName, daysInactive }
    );
  }

  private fallbackAudit(
    repoName: string,
    language: string,
    daysInactive: number,
    dependencyCount: number,
    unpinnedRatio: number,
    cyclomaticEntropy: number
  ): BitrotAuditResult {
    const isCritical = daysInactive > 3650 || (unpinnedRatio > 0.7 && daysInactive > 1800);
    const riskClass = isCritical ? 'Critical' : daysInactive > 1500 ? 'High' : 'Medium';
    const cveRisk = Math.min(0.95, (daysInactive / 5000.0) * 0.7 + (unpinnedRatio * 0.3));
    const yearsInactive = daysInactive / 365.25;

    return {
      repo_name: repoName,
      language,
      days_inactive: daysInactive,
      bitrot_risk_class: riskClass,
      confidence_probabilities: {
        Critical: isCritical ? 0.88 : 0.12,
        High: isCritical ? 0.09 : 0.75,
        Medium: 0.10,
        Low: 0.03,
      },
      cve_vulnerability_risk: parseFloat(cveRisk.toFixed(3)),
      bitrot_index: parseFloat(Math.min(0.99, (daysInactive / 5000.0) * 0.5 + cveRisk * 0.5).toFixed(3)),
      exorcism_complexity: isCritical
        ? 'Severe Necromancy Required (Python 2 to 3 rewrite / AST overhaul)'
        : 'Major Exorcism (Deprecated API upgrade & test synthesis)',
      zombie_dependencies_detected: Math.max(0, Math.floor(dependencyCount * unpinnedRatio)),
      engine: 'PriorLabs TabPFN-3.5 Synthetic Prior (Fallback)',
      time_of_death: {
        estimated_death_year: Math.floor(2026 - yearsInactive),
        years_in_crypt: parseFloat(yearsInactive.toFixed(1)),
        ghost_status: 'Ancient Spectral Codebase (Over a decade in the crypt)',
        resurrection_urgency: 'High',
      },
    };
  }
}
