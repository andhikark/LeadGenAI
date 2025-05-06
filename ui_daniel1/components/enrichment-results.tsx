"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Download, Filter, Search, BarChart3, PieChart } from "lucide-react"

// Mock enriched data for demonstration
const mockEnrichedData = [
  {
    id: 1,
    company: "Acme Inc",
    website: "acme.com",
    industry: "Software",
    businessType: "B2B",
    employees: "50-200",
    revenue: "$10M-$50M",
    founded: "2010",
    location: "San Francisco, CA",
    linkedinUrl: "linkedin.com/company/acme",
    contact: {
      name: "John Smith",
      title: "CTO",
      email: "john@acme.com",
      phone: "+1 (555) 123-4567",
      linkedin: "linkedin.com/in/johnsmith",
    },
    source: "Apollo",
    score: 85,
    enriched: true,
  },
  {
    id: 2,
    company: "TechCorp",
    website: "techcorp.io",
    industry: "SaaS",
    businessType: "B2B",
    employees: "10-50",
    revenue: "$1M-$10M",
    founded: "2018",
    location: "Austin, TX",
    linkedinUrl: "linkedin.com/company/techcorp",
    contact: {
      name: "Sarah Johnson",
      title: "CEO",
      email: "sarah@techcorp.io",
      phone: "+1 (555) 987-6543",
      linkedin: "linkedin.com/in/sarahjohnson",
    },
    source: "Growjo",
    score: 72,
    enriched: true,
  },
  {
    id: 3,
    company: "DataSystems",
    website: "datasystems.co",
    industry: "Data Analytics",
    businessType: "B2B2C",
    employees: "200-500",
    revenue: "$50M-$100M",
    founded: "2005",
    location: "New York, NY",
    linkedinUrl: "linkedin.com/company/datasystems",
    contact: {
      name: "Michael Chen",
      title: "CIO",
      email: "michael@datasystems.co",
      phone: "+1 (555) 456-7890",
      linkedin: "linkedin.com/in/michaelchen",
    },
    source: "Apollo",
    score: 91,
    enriched: true,
  },
  {
    id: 4,
    company: "CloudWorks",
    website: "cloudworks.net",
    industry: "Cloud Services",
    businessType: "B2B",
    employees: "50-200",
    revenue: "$10M-$50M",
    founded: "2012",
    location: "Seattle, WA",
    linkedinUrl: "linkedin.com/company/cloudworks",
    contact: {
      name: "Emily Davis",
      title: "VP of Sales",
      email: "emily@cloudworks.net",
      phone: "+1 (555) 234-5678",
      linkedin: "linkedin.com/in/emilydavis",
    },
    source: "Apollo",
    score: 78,
    enriched: true,
  },
  {
    id: 5,
    company: "AI Solutions",
    website: "aisolutions.ai",
    industry: "Artificial Intelligence",
    businessType: "B2B",
    employees: "10-50",
    revenue: "$1M-$10M",
    founded: "2020",
    location: "Boston, MA",
    linkedinUrl: "linkedin.com/company/aisolutions",
    contact: {
      name: "David Wilson",
      title: "Founder",
      email: "david@aisolutions.ai",
      phone: "+1 (555) 876-5432",
      linkedin: "linkedin.com/in/davidwilson",
    },
    source: "Growjo",
    score: 65,
    enriched: true,
  },
]

export function EnrichmentResults() {
  const [selectedRows, setSelectedRows] = useState<number[]>(mockEnrichedData.map((row) => row.id))
  const [searchTerm, setSearchTerm] = useState("")
  const [view, setView] = useState("table")

  const toggleSelectAll = () => {
    if (selectedRows.length === mockEnrichedData.length) {
      setSelectedRows([])
    } else {
      setSelectedRows(mockEnrichedData.map((row) => row.id))
    }
  }

  const toggleSelectRow = (id: number) => {
    if (selectedRows.includes(id)) {
      setSelectedRows(selectedRows.filter((rowId) => rowId !== id))
    } else {
      setSelectedRows([...selectedRows, id])
    }
  }

  const filteredData = mockEnrichedData.filter(
    (row) =>
      row.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.contact.name.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Enrichment Results</h3>
          <p className="text-sm text-muted-foreground">{mockEnrichedData.length} leads enriched successfully</p>
        </div>
        <div className="flex items-center gap-2">
          <Tabs value={view} onValueChange={setView} className="w-[400px]">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="table">
                <BarChart3 className="mr-2 h-4 w-4" />
                Table View
              </TabsTrigger>
              <TabsTrigger value="cards">
                <PieChart className="mr-2 h-4 w-4" />
                Card View
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search results..."
              className="w-64 pl-8"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Select defaultValue="csv">
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Format" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="csv">CSV</SelectItem>
              <SelectItem value="excel">Excel</SelectItem>
              <SelectItem value="json">JSON</SelectItem>
            </SelectContent>
          </Select>
          <Button
            className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600"
            disabled={selectedRows.length === 0}
          >
            <Download className="mr-2 h-4 w-4" />
            Export Selected
          </Button>
        </div>
      </div>

      <TabsContent value="table" className="mt-0">
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedRows.length === mockEnrichedData.length && mockEnrichedData.length > 0}
                    onCheckedChange={toggleSelectAll}
                  />
                </TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Industry</TableHead>
                <TableHead>Business Type</TableHead>
                <TableHead>Employees</TableHead>
                <TableHead>Revenue</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredData.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>
                    <Checkbox checked={selectedRows.includes(row.id)} onCheckedChange={() => toggleSelectRow(row.id)} />
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{row.company}</div>
                    <div className="text-sm text-muted-foreground">{row.website}</div>
                  </TableCell>
                  <TableCell>{row.industry}</TableCell>
                  <TableCell>{row.businessType}</TableCell>
                  <TableCell>{row.employees}</TableCell>
                  <TableCell>{row.revenue}</TableCell>
                  <TableCell>
                    <div className="font-medium">{row.contact.name}</div>
                    <div className="text-sm text-muted-foreground">{row.contact.title}</div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{row.source}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        row.score >= 80
                          ? "bg-green-100 text-green-800"
                          : row.score >= 60
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-red-100 text-red-800"
                      }
                    >
                      {row.score}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </TabsContent>

      <TabsContent value="cards" className="mt-0">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredData.map((row) => (
            <Card key={row.id} className="overflow-hidden">
              <CardContent className="p-0">
                <div className="p-4 border-b flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{row.company}</h4>
                    <p className="text-sm text-muted-foreground">{row.website}</p>
                  </div>
                  <Checkbox checked={selectedRows.includes(row.id)} onCheckedChange={() => toggleSelectRow(row.id)} />
                </div>
                <div className="p-4 space-y-4">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-muted-foreground">Industry</p>
                      <p>{row.industry}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Business Type</p>
                      <p>{row.businessType}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Employees</p>
                      <p>{row.employees}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Revenue</p>
                      <p>{row.revenue}</p>
                    </div>
                  </div>

                  <div className="pt-2 border-t">
                    <p className="text-muted-foreground text-sm">Contact</p>
                    <p className="font-medium">{row.contact.name}</p>
                    <p className="text-sm">{row.contact.title}</p>
                    <p className="text-sm">{row.contact.email}</p>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t">
                    <Badge variant="outline">{row.source}</Badge>
                    <Badge
                      className={
                        row.score >= 80
                          ? "bg-green-100 text-green-800"
                          : row.score >= 60
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-red-100 text-red-800"
                      }
                    >
                      Score: {row.score}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {selectedRows.length} of {mockEnrichedData.length} selected for export
        </div>
        <Button
          variant="outline"
          onClick={() => setSelectedRows(mockEnrichedData.map((row) => row.id))}
          disabled={selectedRows.length === mockEnrichedData.length}
        >
          Select All
        </Button>
      </div>
    </div>
  )
}
