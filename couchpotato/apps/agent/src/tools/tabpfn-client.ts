/**
 * TabPFN-3.5 MCP Client Tool
 * Interfaces with the Python FastMCP server to invoke few-shot tax classification
 * and quantile bill spike anomaly detection.
 */

import { spawnSync } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { traceSpan } from '../telemetry/sentry.js';

export interface TaxClassificationResult {
  vendor: string;
  amount: number;
  description: string;
  predicted_category: string;
  confidence: number;
  class_probabilities: Record<string, number>;
  is_deductible: boolean;
  classification_engine: string;
  historical_records_used: number;
}

export interface BillSpikeResult {
  vendor: string;
  current_amount: number;
  historical_median: number;
  historical_mean: number;
  expected_range: [number, number];
  anomaly_score: number;
  is_spike: boolean;
  percent_change_vs_median: number;
  explanation: string;
  historical_samples_count: number;
  detector_engine: string;
}

export class TabPfnClient {
  private serverUrl: string;
  private pythonServerPath: string;

  constructor(serverUrl: string = process.env.TABPFN_SERVER_URL || 'http://localhost:8001') {
    this.serverUrl = serverUrl;
    const candidates = [
      path.resolve(process.cwd(), 'services', 'tabpfn-service', 'server.py'),
      path.resolve(process.cwd(), '..', '..', 'services', 'tabpfn-service', 'server.py'),
      path.resolve(__dirname, '..', '..', '..', 'services', 'tabpfn-service', 'server.py'),
      path.resolve(__dirname, '..', '..', '..', '..', 'services', 'tabpfn-service', 'server.py'),
      path.resolve(process.cwd(), '..', 'services', 'tabpfn-service', 'server.py'),
    ];

    const found = candidates.find(p => fs.existsSync(p));
    this.pythonServerPath = found || candidates[0];
  }

  /**
   * Classify an expense into IRS Schedule C category using TabPFN
   */
  async classifyExpense(
    vendor: string,
    amount: number,
    description: string = '',
    historyCsvPath?: string
  ): Promise<TaxClassificationResult> {
    return traceSpan('tabpfn-classify-expense', 'ml.classify', async () => {
      // 1. Try MCP / HTTP Endpoint if running
      try {
        const response = await fetch(`${this.serverUrl}/call/classify_expense`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            arguments: {
              vendor,
              amount,
              description,
              history_csv_path: historyCsvPath || '',
            },
          }),
          signal: AbortSignal.timeout(2000),
        });

        if (response.ok) {
          const json: any = await response.json();
          return json.result || json;
        }
      } catch {
        // Fallback to local python invoker
      }

      // 2. Local Python In-Process Direct Invocation (Fast, Zero-Network Fallback)
      return this.invokePythonTool<TaxClassificationResult>('classify_expense', {
        vendor,
        amount,
        description,
        history_csv_path: historyCsvPath || '',
      });
    }, { vendor, amount, description });
  }

  /**
   * Detect abnormal billing surge or seasonal anomaly using TabPFN
   */
  async detectBillSpike(
    vendor: string,
    currentAmount: number,
    historyCsvPath?: string
  ): Promise<BillSpikeResult> {
    return traceSpan('tabpfn-detect-bill-spike', 'ml.anomaly', async () => {
      // 1. Try MCP / HTTP Endpoint if running
      try {
        const response = await fetch(`${this.serverUrl}/call/detect_bill_spike`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            arguments: {
              vendor,
              current_amount: currentAmount,
              history_csv_path: historyCsvPath || '',
            },
          }),
          signal: AbortSignal.timeout(2000),
        });

        if (response.ok) {
          const json: any = await response.json();
          return json.result || json;
        }
      } catch {
        // Fallback to local python invoker
      }

      // 2. Local Python In-Process Direct Invocation
      return this.invokePythonTool<BillSpikeResult>('detect_bill_spike', {
        vendor,
        current_amount: currentAmount,
        history_csv_path: historyCsvPath || '',
      });
    }, { vendor, currentAmount });
  }

  /**
   * Direct Python execution fallback using server.py functions
   */
  private invokePythonTool<T>(toolName: string, args: Record<string, any>): T {
    const serverDir = path.dirname(this.pythonServerPath);
    const invokerPath = path.resolve(serverDir, 'invoker.py');
    let pythonBin = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
    if (process.env.PYTHON_PATH && fs.existsSync(process.env.PYTHON_PATH)) {
      pythonBin = process.env.PYTHON_PATH;
    }

    const result = spawnSync(pythonBin, [invokerPath, toolName], {
      cwd: serverDir,
      encoding: 'utf-8',
      env: { ...process.env, PYTHONPATH: serverDir },
      input: JSON.stringify(args),
      shell: false,
    });

    if (result.error) {
      throw result.error;
    }

    const output = (result.stdout || '') + (result.stderr || '');
    const match = output.match(/__RESULT_START__(.*)__RESULT_END__/);
    if (!match) {
      throw new Error(`Failed to parse Python TabPFN output: ${output}`);
    }

    return JSON.parse(match[1]) as T;
  }
}
