import { CheckCircle2, FileUp, LoaderCircle, ShieldCheck } from 'lucide-react'
import { useRef, useState, type ChangeEvent } from 'react'
import { uploadDocument } from '../services/api'

export default function AdminUploadPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [status, setStatus] = useState<string | null>(null)

  const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null

    if (!file) {
      return
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setSelectedFile(null)
      setStatus('Only PDF files are allowed for upload.')
      event.target.value = ''
      return
    }

    setSelectedFile(file)
    setStatus(`Ready to upload: ${file.name}`)
    event.target.value = ''
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setStatus('Please choose a PDF file first.')
      return
    }

    setIsUploading(true)
    setStatus('Uploading document...')

    try {
      const result = await uploadDocument(selectedFile)
      setStatus(
        result.success
          ? `Document uploaded successfully: ${result.filename ?? selectedFile.name}`
          : 'Document upload failed.',
      )
      setSelectedFile(null)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to upload the document.'
      setStatus(message)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="flex h-full items-center justify-center overflow-y-auto px-4 py-10 sm:px-6 lg:px-8">
      <div className="w-full max-w-2xl rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_18px_45px_rgba(15,23,42,0.08)] sm:p-8">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
            <ShieldCheck size={24} />
          </div>
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-emerald-600">Admin access</p>
            <h2 className="text-2xl font-semibold text-slate-900">Upload knowledge document</h2>
          </div>
        </div>

        <p className="mt-4 text-sm text-slate-600">
          This page is for administrators only. Upload a PDF to add it to the ICog knowledge base.
        </p>

        <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-slate-700 shadow-sm">
            <FileUp size={24} />
          </div>

          <p className="mt-4 text-base font-medium text-slate-800">
            {selectedFile ? selectedFile.name : 'No file selected'}
          </p>

          <div className="mt-5 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-100"
            >
              Choose PDF
            </button>

            <button
              type="button"
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
              className="inline-flex items-center justify-center rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-emerald-200 transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400 disabled:shadow-none"
            >
              {isUploading ? (
                <>
                  <LoaderCircle size={16} className="mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                'Upload document'
              )}
            </button>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleFileSelect}
          />
        </div>

        {status && (
          <div className="mt-5 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700">
            {status.toLowerCase().includes('success') || status.toLowerCase().includes('ready to upload') ? (
              <CheckCircle2 size={16} className="text-emerald-600" />
            ) : (
              <FileUp size={16} className="text-slate-500" />
            )}
            <span>{status}</span>
          </div>
        )}
      </div>
    </div>
  )
}
