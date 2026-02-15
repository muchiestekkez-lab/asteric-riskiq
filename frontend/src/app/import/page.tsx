'use client';

import { useState, useRef } from 'react';
import Header from '@/components/layout/Header';
import { importPatientsCSV } from '@/lib/api';
import {
  Upload, FileText, CheckCircle, AlertCircle, Download,
  ArrowRight, Loader2,
} from 'lucide-react';

export default function ImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{
    imported: number;
    errors: string[];
    total_errors: number;
    message: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      if (!selected.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        return;
      }
      setFile(selected);
      setError(null);
      setResult(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      if (!dropped.name.endsWith('.csv')) {
        setError('Please drop a CSV file');
        return;
      }
      setFile(dropped);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setError(null);
    setResult(null);

    try {
      setUploading(true);
      const data = await importPatientsCSV(file);
      setResult(data);
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
    } catch (err: any) {
      setError(err.message || 'Import failed');
    } finally {
      setUploading(false);
    }
  };

  const sampleCSV = `first_name,last_name,age,gender,diagnosis_code,diagnosis_name,ward,admission_date,discharge_date,length_of_stay,chronic_conditions,medication_count,num_previous_admissions,bp_systolic,bp_diastolic,heart_rate,was_readmitted
John,Smith,67,M,I50.9,Heart failure,Cardiology,2025-01-10,2025-01-15,5,Diabetes;Hypertension,8,2,145,90,88,yes
Jane,Doe,54,F,J44.1,COPD with acute exacerbation,Pulmonology,2025-01-12,2025-01-18,6,COPD;Asthma,5,1,130,85,76,no`;

  const downloadSample = () => {
    const blob = new Blob([sampleCSV], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'riskiq_sample_import.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-surface-50">
      <Header title="Import Patients" subtitle="Bulk upload patient records from CSV files" />

      <div className="p-6 max-w-3xl space-y-6">

        {/* Instructions */}
        <div className="card p-6">
          <h3 className="text-base font-semibold text-gray-900 mb-3">CSV Format Guide</h3>
          <p className="text-sm text-gray-600 mb-4">
            Upload a CSV file with patient records. The system automatically maps common column names.
            At minimum, include <strong>first_name</strong> and <strong>last_name</strong> columns.
          </p>

          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Supported Columns</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-1 text-xs text-gray-600">
              {[
                'first_name, last_name', 'age, gender', 'mrn, date_of_birth',
                'diagnosis_code, diagnosis_name', 'ward, insurance',
                'admission_date, discharge_date', 'length_of_stay',
                'chronic_conditions (;)', 'medication_count',
                'num_previous_admissions', 'bp_systolic, bp_diastolic',
                'heart_rate, temperature', 'oxygen_saturation, bmi',
                'hemoglobin, creatinine, glucose', 'was_readmitted (yes/no)',
                'clinical_notes', 'smoking_status',
              ].map((col, i) => (
                <span key={i} className="font-mono">{col}</span>
              ))}
            </div>
          </div>

          <button onClick={downloadSample} className="btn-secondary flex items-center gap-2 text-sm">
            <Download className="w-4 h-4" />
            Download Sample CSV
          </button>
        </div>

        {/* Upload Area */}
        <div className="card p-6">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-gray-200 rounded-xl p-10 text-center hover:border-brand-400 transition-colors cursor-pointer"
            onClick={() => inputRef.current?.click()}
          >
            <input ref={inputRef} type="file" accept=".csv" onChange={handleFileChange} className="hidden" />
            <Upload className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-sm font-medium text-gray-700">
              {file ? file.name : 'Drop CSV file here or click to browse'}
            </p>
            {file && (
              <p className="text-xs text-gray-400 mt-1">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            )}
            {!file && (
              <p className="text-xs text-gray-400 mt-1">Supports .csv files</p>
            )}
          </div>

          {file && (
            <div className="mt-4 flex items-center gap-3">
              <button onClick={handleUpload} disabled={uploading} className="btn-primary flex items-center gap-2">
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <ArrowRight className="w-4 h-4" />
                    Import Patients
                  </>
                )}
              </button>
              <button onClick={() => { setFile(null); if (inputRef.current) inputRef.current.value = ''; }}
                className="btn-secondary">Cancel</button>
            </div>
          )}
        </div>

        {/* Results */}
        {result && (
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="w-6 h-6 text-emerald-600" />
              <div>
                <h3 className="text-base font-semibold text-gray-900">Import Complete</h3>
                <p className="text-sm text-gray-600">{result.message}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-emerald-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-emerald-700">{result.imported}</p>
                <p className="text-xs text-emerald-600 mt-1">Patients Imported</p>
              </div>
              <div className="bg-red-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-red-700">{result.total_errors}</p>
                <p className="text-xs text-red-600 mt-1">Errors</p>
              </div>
            </div>

            {result.errors.length > 0 && (
              <div className="bg-red-50 rounded-lg p-4">
                <p className="text-xs font-medium text-red-700 mb-2">Errors (showing first 20):</p>
                <ul className="space-y-1">
                  {result.errors.map((err, i) => (
                    <li key={i} className="text-xs text-red-600 flex items-start gap-1">
                      <AlertCircle className="w-3 h-3 mt-0.5 shrink-0" />
                      {err}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 border border-red-200">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Training Tip */}
        <div className="card p-6 bg-brand-50 border-brand-200">
          <h4 className="text-sm font-semibold text-brand-800 mb-2">Training the AI Model</h4>
          <p className="text-xs text-brand-700">
            Once you have 50+ patients with known readmission outcomes (the "was_readmitted" column),
            go to <strong>Analytics</strong> and click <strong>Train Model</strong>. The AI will learn from your
            hospital's data and start generating real risk predictions for new patients.
          </p>
        </div>
      </div>
    </div>
  );
}
