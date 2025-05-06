"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Download, Filter, Search } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Mock data for demonstration
const mockResults = [
  {
    id: 1,
    company: "Acme Inc",
    website: "acme.com",
    location: "San Francisco, CA",
    industry: "Software",
    revenue: "$10M-$50M",
    employees: "50-200",
    decisionMaker: {
      name: "John Smith",
      title: "CTO",
      email: "john@acme.com",
      linkedin: "linkedin.com/in/johnsmith",
      phone: "+1 (555) 123-4567",
    },
  },
  {
    id: 2,
    company: "TechCorp",
    website: "techcorp.io",
    location: "Austin, TX",
    industry: "SaaS",
    revenue: "$1M-$10M",
    employees: "10-50",
    decisionMaker: {
      name: "Sarah Johnson",
      title: "CEO",
      email: "sarah@techcorp.io",
      linkedin: "linkedin.com/in/sarahjohnson",
      phone: "+1 (555) 987-6543",
    },
  },
  {
    id: 3,
    company: "DataSystems",
    website: "datasystems.co",
    location: "New York, NY",
    industry: "Data Analytics",
    revenue: "$50M-$100M",
    employees: "200-500",
    decisionMaker: {
      name: "Michael Chen",
      title: "CIO",
      email: "michael@datasystems.co",
      linkedin: "linkedin.com/in/michaelchen",
      phone: "+1 (555) 456-7890",
    },
  },
]

export function ScraperResults() {
  const [selectedRows, setSelectedRows] = useState<number[]>([])
  const [searchTerm, setSearchTerm] = useState("")

  const toggleSelectAll = () => {
    if (selectedRows.length === mockResults.length) {
      setSelectedRows([])
    } else {
      setSelectedRows(mockResults.map((result) => result.id))
    }
  }

  const toggleSelectRow = (id: number) => {
    if (selectedRows.includes(id)) {
      setSelectedRows(selectedRows.filter((rowId) => rowId !== id))
    } else {
      setSelectedRows([...selectedRows, id])
    }
  }

  const filteredResults = mockResults.filter(
    (result) =>
      result.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.decisionMaker.name.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Scraper Results</CardTitle>
            <CardDescription>{mockResults.length} companies found</CardDescription>
          </div>
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
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedRows.length === mockResults.length && mockResults.length > 0}
                    onCheckedChange={toggleSelectAll}
                  />
                </TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Industry</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Revenue</TableHead>
                <TableHead>Employees</TableHead>
                <TableHead>Decision Maker</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredResults.length > 0 ? (
                filteredResults.map((result) => (
                  <TableRow key={result.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedRows.includes(result.id)}
                        onCheckedChange={() => toggleSelectRow(result.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{result.company}</div>
                      <div className="text-sm text-muted-foreground">{result.website}</div>
                    </TableCell>
                    <TableCell>{result.industry}</TableCell>
                    <TableCell>{result.location}</TableCell>
                    <TableCell>{result.revenue}</TableCell>
                    <TableCell>{result.employees}</TableCell>
                    <TableCell>
                      <div className="font-medium">{result.decisionMaker.name}</div>
                      <div className="text-sm text-muted-foreground">{result.decisionMaker.title}</div>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    No results found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <div className="text-sm text-muted-foreground">
          {selectedRows.length} of {mockResults.length} selected
        </div>
        <div className="flex gap-2">
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
      </CardFooter>
    </Card>
  )
}
