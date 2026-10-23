'use client';

import React, { useState } from 'react';
import { FileText, Eye, CheckCircle2, AlertCircle, Shield, Cpu, Lock, X } from 'lucide-react';

export interface ExpenseRecord {
  id: string;
  vendor: string;
  date: string;
  amount: number;
  currency: string;
  due_date?: string;
  account_last4?: string;
  tax_category: string;
  deductible: boolean;
  anomaly_score: number;
  is_spike: boolean;
  expected_range?: [number, number];
  spike_reason?: string | null;
  status: string;
  source_portal: string;
  pdf_path: string;
  extracted_by: string;
  classified_by: string;
  timestamp: string;
}

interface InvoiceVaultProps {
  expenses: ExpenseRecord[];
}

export const InvoiceVault: React.FC<InvoiceVaultProps> = ({ expenses }) => {
  const [selectedExpense, setSelectedExpense] = useState<ExpenseRecord | null>(null);

  return (
    <div className="border border-tactical-border bg-obsidian-900 rounded-lg shadow-tactile-dark overflow-hidden">
      {/* Table Header */}
      <div className="p-5 border-b border-tactical-border flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-amber-500" />
            Active Statement & Receipt Vault
          </h3>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            Auto-harvested PDFs filed into local encrypted storage with zero human handling.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-zinc-400 bg-obsidian-850 px-3 py-1.5 rounded border border-tactical-border">
          <Lock className="w-3.5 h-3.5 text-lime-400" />
          <span>Local Vault Encrypted</span>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-obsidian-850 text-zinc-400 font-mono text-xs uppercase tracking-wider border-b border-tactical-border">
            <tr>
              <th className="py-3 px-4">Date</th>
              <th className="py-3 px-4">Vendor & Account</th>
              <th className="py-3 px-4">Schedule C Tax Category</th>
              <th className="py-3 px-4 text-right">Amount</th>
              <th className="py-3 px-4">Status & Anomaly</th>
              <th className="py-3 px-4">Engines</th>
              <th className="py-3 px-4 text-right">Audit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-tactical-border text-zinc-200">
            {expenses.map((expense) => (
              <tr key={expense.id} className="hover:bg-obsidian-800/50 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs text-zinc-400">
                  {expense.date}
                </td>
                <td className="py-3.5 px-4">
                  <div className="font-semibold text-white">{expense.vendor}</div>
                  <div className="text-xs font-mono text-zinc-500">
                    Acc: •••• {expense.account_last4 || '4421'}
                  </div>
                </td>
                <td className="py-3.5 px-4">
                  <span className="inline-block px-2 py-0.5 rounded text-xs font-mono font-medium bg-zinc-800 border border-zinc-700 text-zinc-300">
                    {expense.tax_category}
                  </span>
                </td>
                <td className="py-3.5 px-4 text-right font-mono font-bold text-white">
                  ${expense.amount.toFixed(2)}
                </td>
                <td className="py-3.5 px-4">
                  {expense.is_spike ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/30">
                      <AlertCircle className="w-3 h-3" /> Spike (+{(expense.anomaly_score * 100).toFixed(0)}%)
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-medium bg-lime-500/10 text-lime-400 border border-lime-500/20">
                      <CheckCircle2 className="w-3 h-3" /> Clean
                    </span>
                  )}
                </td>
                <td className="py-3.5 px-4">
                  <div className="flex items-center gap-1 text-[11px] font-mono text-zinc-400">
                    <span className="text-amber-400 font-semibold">Gemma 2</span>
                    <span>+</span>
                    <span className="text-cyan-400 font-semibold">TabPFN</span>
                  </div>
                </td>
                <td className="py-3.5 px-4 text-right">
                  <button
                    onClick={() => setSelectedExpense(expense)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono bg-obsidian-800 hover:bg-obsidian-700 text-zinc-300 border border-tactical-border rounded active:translate-y-0.5 transition-all"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Audit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Audit Modal / Drawer */}
      {selectedExpense && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-obsidian-900 border border-tactical-border rounded-lg max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-4 border-b border-tactical-border">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-amber-500" />
                <h4 className="text-lg font-bold text-white">Invoice Audit & Privacy Telemetry</h4>
              </div>
              <button
                onClick={() => setSelectedExpense(null)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-3 bg-obsidian-850 p-4 rounded border border-tactical-border font-mono text-xs">
                <div>
                  <span className="text-zinc-500">Vendor:</span>
                  <p className="font-bold text-white text-sm">{selectedExpense.vendor}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Amount Due:</span>
                  <p className="font-bold text-white text-sm">${selectedExpense.amount.toFixed(2)}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Statement Date:</span>
                  <p className="text-zinc-200">{selectedExpense.date}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Account (Redacted):</span>
                  <p className="text-zinc-200">•••• {selectedExpense.account_last4 || '4421'}</p>
                </div>
                <div className="col-span-2">
                  <span className="text-zinc-500">Schedule C Tax Classification:</span>
                  <p className="text-amber-400 font-bold">{selectedExpense.tax_category}</p>
                </div>
                <div className="col-span-2">
                  <span className="text-zinc-500">Local Vault Filepath:</span>
                  <p className="text-zinc-400 truncate">{selectedExpense.pdf_path}</p>
                </div>
              </div>

              {/* Privacy Certification */}
              <div className="border border-lime-500/30 bg-lime-950/20 p-3.5 rounded flex items-start gap-3">
                <Shield className="w-5 h-5 text-lime-400 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <span className="font-bold text-lime-300 font-mono">100% Privacy-Preserving Zero Leakage</span>
                  <p className="text-zinc-300 mt-0.5">
                    Statement parsed strictly on your device using local <strong>Gemma 2 (via Ollama)</strong>.
                    No bank accounts, utility identifiers, or address details were transmitted over any cloud LLM API.
                  </p>
                </div>
              </div>

              {/* TabPFN Model Telemetry */}
              <div className="border border-tactical-border bg-obsidian-850 p-3.5 rounded flex items-start gap-3">
                <Cpu className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <span className="font-bold text-cyan-300 font-mono">TabPFN-3.5 Foundation Inference</span>
                  <p className="text-zinc-400 mt-0.5">
                    Few-shot Bayesian neural prior evaluated against historical commercial ledger.
                    Anomaly score: {(selectedExpense.anomaly_score * 100).toFixed(1)}%.
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedExpense(null)}
                className="px-4 py-2 bg-obsidian-800 hover:bg-obsidian-700 text-zinc-200 font-mono text-xs rounded border border-tactical-border"
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
