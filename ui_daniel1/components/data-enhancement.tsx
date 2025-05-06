"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Stepper } from "@/components/stepper"
import { FileUpload } from "@/components/file-upload"
import { ColumnMapping } from "@/components/column-mapping"
import { DataPreview } from "@/components/data-preview"
import { EnrichmentOptions } from "@/components/enrichment-options"
import { EnrichmentResults } from "@/components/enrichment-results"

export function DataEnhancement() {
  const [currentStep, setCurrentStep] = useState(0)
  const [file, setFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)

  const steps = [
    { title: "Upload File", description: "Upload a CSV file with lead data" },
    { title: "Map Columns", description: "Match CSV columns to standard fields" },
    { title: "Preview Data", description: "Review and select rows to enhance" },
    { title: "Configure Enrichment", description: "Set up enrichment options" },
    { title: "Results", description: "View and export enhanced data" },
  ]

  const handleFileUpload = (uploadedFile: File) => {
    setFile(uploadedFile)
  }

  const handleNext = () => {
    if (currentStep === 3) {
      // Start enrichment process
      setIsProcessing(true)
      setProgress(0)

      // Simulate progress
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval)
            setIsProcessing(false)
            setCurrentStep(4)
            return 100
          }
          return prev + 5
        })
      }, 300)
    } else {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    setCurrentStep(currentStep - 1)
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return <FileUpload onFileUpload={handleFileUpload} />
      case 1:
        return <ColumnMapping />
      case 2:
        return <DataPreview />
      case 3:
        return <EnrichmentOptions />
      case 4:
        return <EnrichmentResults />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Data Enhancement</h2>
        <p className="text-muted-foreground">Normalize and enrich lead data using multiple sources</p>
      </div>

      <Stepper currentStep={currentStep} steps={steps} />

      {isProcessing ? (
        <Card>
          <CardHeader>
            <CardTitle>Enriching Data</CardTitle>
            <CardDescription>Enhancing your lead data with Apollo and Growjo</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
              <p className="text-sm text-muted-foreground mt-2">
                This may take several minutes depending on the size of your dataset
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="pt-6">{renderStepContent()}</CardContent>
          <CardFooter className="flex justify-between">
            <Button variant="outline" onClick={handleBack} disabled={currentStep === 0}>
              Back
            </Button>
            <Button
              className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600"
              onClick={handleNext}
              disabled={currentStep === 4 || (currentStep === 0 && !file)}
            >
              {currentStep === 3 ? "Start Enrichment" : currentStep === 4 ? "Export Data" : "Next"}
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  )
}
