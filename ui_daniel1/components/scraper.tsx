"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Progress } from "@/components/ui/progress"
import { ScraperResults } from "@/components/scraper-results"
import { Upload, FileUp, Settings2 } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible"

export function Scraper() {
  const [inputMethod, setInputMethod] = useState("manual")
  const [isScrapingActive, setIsScrapingActive] = useState(false)
  const [progress, setProgress] = useState(0)
  const [showResults, setShowResults] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  const handleStartScraping = () => {
    setIsScrapingActive(true)
    setProgress(0)
    setShowResults(false)

    // Simulate progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsScrapingActive(false)
          setShowResults(true)
          return 100
        }
        return prev + 10
      })
    }, 500)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Growjo Scraper</h2>
          <p className="text-muted-foreground">Extract company information and decision maker details from Growjo</p>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="icon" onClick={() => setShowSettings(!showSettings)}>
                <Settings2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Scraper Settings</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <Collapsible open={showSettings} onOpenChange={setShowSettings} className="mb-4">
        <CollapsibleContent>
          <Card>
            <CardHeader>
              <CardTitle>Scraper Settings</CardTitle>
              <CardDescription>Configure how the scraper operates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="headless">Headless Mode</Label>
                  <p className="text-sm text-muted-foreground">Run browser in background without UI</p>
                </div>
                <Switch id="headless" defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="proxy">Use Proxy</Label>
                  <p className="text-sm text-muted-foreground">Route requests through proxy servers</p>
                </div>
                <Switch id="proxy" />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="delay">Request Delay (ms)</Label>
                  <p className="text-sm text-muted-foreground">Time between requests</p>
                </div>
                <Input id="delay" type="number" defaultValue="2000" className="w-24" />
              </div>
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>

      <Card>
        <CardHeader>
          <CardTitle>Input Companies</CardTitle>
          <CardDescription>Enter company names to scrape information from Growjo</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={inputMethod} onValueChange={setInputMethod} className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="manual">Manual Input</TabsTrigger>
              <TabsTrigger value="csv">CSV Upload</TabsTrigger>
            </TabsList>
            <TabsContent value="manual">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="companies">Company Names</Label>
                  <Textarea id="companies" placeholder="Enter company names, one per line" className="min-h-32" />
                  <p className="text-sm text-muted-foreground">Example: Vercel, Stripe, Airbnb</p>
                </div>
              </div>
            </TabsContent>
            <TabsContent value="csv">
              <div className="flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-12 text-center">
                <Upload className="h-8 w-8 text-muted-foreground mb-4" />
                <h3 className="font-medium mb-1">Upload CSV File</h3>
                <p className="text-sm text-muted-foreground mb-4">Drag and drop or click to browse</p>
                <Button className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600">
                  <FileUp className="mr-2 h-4 w-4" />
                  Browse Files
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline">Clear</Button>
          <Button
            className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600"
            onClick={handleStartScraping}
            disabled={isScrapingActive}
          >
            Start Scraping
          </Button>
        </CardFooter>
      </Card>

      {isScrapingActive && (
        <Card>
          <CardHeader>
            <CardTitle>Scraping in Progress</CardTitle>
            <CardDescription>Extracting data from Growjo</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
              <p className="text-sm text-muted-foreground mt-2">
                This may take a few minutes depending on the number of companies
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {showResults && <ScraperResults />}
    </div>
  )
}
