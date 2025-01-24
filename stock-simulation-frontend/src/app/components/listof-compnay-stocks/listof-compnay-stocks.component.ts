import { Component, OnInit, ViewChild, AfterViewInit, TemplateRef } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { ToastrService } from 'ngx-toastr';
import { MatDialog } from '@angular/material/dialog';
import { saveAs } from 'file-saver';
import { forkJoin } from 'rxjs';

interface Company {
  id: number;
  company_name: string;
  sector: string;
  last_updated: string;
}

interface Stock {
  id: number;
  company: number;
  ticker_symbol: string;
  total_shares: number;
  current_price: string;
  available_shares: number;
  max_trader_buy_limit: number;
  created_at: string;
  company_name: string;
}

interface CombinedStock {
  id: number;
  company_id: number;
  company_name: string;
  sector: string;
  ticker_symbol: string;
  total_shares: number;
  current_price: string;
  available_shares: number;
  max_trader_buy_limit: number;
  created_at: string;
  last_updated: string;
}

@Component({
  selector: 'app-listofCompnayStocks',
  templateUrl: './listof-compnay-stocks.component.html',
  styleUrls: ['./listof-compnay-stocks.component.css']
})
export class ListofCompnayStocksComponent implements OnInit, AfterViewInit {
  displayedColumns: string[] = [
    'id',
    'company_name',
    'sector',
    'ticker_symbol',
    'total_shares',
    'current_price',
    'available_shares',
    'max_trader_buy_limit',
    'created_at',
    'last_updated',
    'actions'
  ];

  dataSource = new MatTableDataSource<CombinedStock>([]);
  isLoading = true;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private http: HttpClient,
    private toastr: ToastrService,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.fetchCompaniesAndStocks();
  }

  /**
   * Ensures MatPaginator and MatSort are available after the view initializes.
   */
  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;

    // Custom filter predicate to allow filtering by multiple fields
    this.dataSource.filterPredicate = (data: CombinedStock, filter: string) => {
      const dataStr = `${data.company_name} ${data.ticker_symbol} ${data.sector}`.toLowerCase();
      return dataStr.includes(filter);
    };
  }

  /**
   * Fetches both companies and stocks concurrently, then merges them into a CombinedStock array.
   */
  fetchCompaniesAndStocks(): void {
    this.isLoading = true;

    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      this.isLoading = false;
      return;
    }

    const headers = new HttpHeaders({ Authorization: `Bearer ${accessToken}` });
    const companiesEndpoint = 'http://localhost:8000/api/stocks/companies/';
    const stocksEndpoint = 'http://localhost:8000/api/stocks/stocks/';

    forkJoin({
      companies: this.http.get<Company[]>(companiesEndpoint, { headers }),
      stocks: this.http.get<Stock[]>(stocksEndpoint, { headers })
    }).subscribe({
      next: ({ companies, stocks }) => {
        // Combine the data based on company ID
        const combinedData: CombinedStock[] = stocks.map(stock => {
          const company = companies.find(c => c.id === stock.company);
          return {
            id: stock.id,
            company_id: stock.company,
            company_name: company ? company.company_name : 'Unknown',
            sector: company ? company.sector : 'Unknown',
            ticker_symbol: stock.ticker_symbol,
            total_shares: stock.total_shares,
            current_price: stock.current_price,
            available_shares: stock.available_shares,
            max_trader_buy_limit: stock.max_trader_buy_limit,
            created_at: stock.created_at,
            last_updated: company ? company.last_updated : 'Unknown'
          };
        });

        this.dataSource.data = combinedData;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error fetching companies or stocks:', err);
        this.toastr.error('Failed to fetch companies or stocks.', 'Error');
        this.isLoading = false;
      }
    });
  }

  /**
   * Filters the table based on user input.
   */
  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();

    // Reset to the first page if filtering
    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  /**
   * Exports the table data to CSV.
   */
  exportToCSV(): void {
    if (this.dataSource.data.length === 0) {
      this.toastr.info('No data available to export.', 'Info');
      return;
    }

    const headers = this.displayedColumns.filter(col => col !== 'actions');
    const csvRows = [];

    // Add header row
    csvRows.push(headers.join(','));

    // Add data rows
    this.dataSource.filteredData.forEach(stock => {
      const row = headers.map(header => {
        let cell = (stock as any)[header];
        if (typeof cell === 'string') {
          // Escape double quotes
          cell = cell.replace(/"/g, '""');
          // Wrap in double quotes if it contains a comma
          if (cell.includes(',')) {
            cell = `"${cell}"`;
          }
        }
        return cell;
      });
      csvRows.push(row.join(','));
    });

    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const filename = 'listofCompnayStocks_export.csv';
    saveAs(blob, filename);
    this.toastr.success('Stocks exported successfully.', 'Success');
  }

  /**
   * Prints the table content inside #print-section.
   */
  printTable(): void {
    const printContents = document.getElementById('print-section')?.innerHTML;
    if (!printContents) {
      this.toastr.error('Nothing to print.', 'Error');
      return;
    }

    const originalContents = document.body.innerHTML;
    document.body.innerHTML = printContents;

    window.print();

    // Restore original contents after printing
    document.body.innerHTML = originalContents;
    window.location.reload(); // Reload to re-initialize Angular bindings
  }

  /**
   * Placeholder action: Allows stock addition for a company.
   */
  allowStockAddition(stock: CombinedStock): void {
    this.toastr.info(`Allowing stock addition for ${stock.company_name}`, 'Info');
    // Implement real logic here...
  }

  /**
   * Sends a request to unlist the company from the platform.
   */
  unlistCompany(stock: CombinedStock): void {
    if (!confirm(`Are you sure you want to unlist company "${stock.company_name}"?`)) {
      return;
    }

    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      return;
    }

    const headers = new HttpHeaders({ Authorization: `Bearer ${accessToken}` });
    const endpoint = `http://localhost:8000/api/stocks/companies/${stock.company_id}/unlist/`;

    this.http.post(endpoint, {}, { headers }).subscribe({
      next: () => {
        this.toastr.success(`Company "${stock.company_name}" unlisted successfully.`, 'Success');
        this.removeStockFromDataSource(stock.id);
      },
      error: (err) => {
        console.error('Error unlisting company:', err);
        this.displayBackendErrors(err);
      }
    });
  }

  /**
   * Helper method to remove a stock from the data source.
   */
  removeStockFromDataSource(id: number): void {
    this.dataSource.data = this.dataSource.data.filter(stock => stock.id !== id);
  }

  /**
   * Displays backend error messages using ToastrService.
   */
  private displayBackendErrors(err: any): void {
    if (err.error && typeof err.error === 'object') {
      Object.keys(err.error).forEach((key) => {
        const messages = err.error[key];
        messages.forEach((message: string) => {
          this.toastr.error(`${key}: ${message}`, 'Error');
        });
      });
    } else if (err.error && typeof err.error === 'string') {
      this.toastr.error(err.error, 'Error');
    } else {
      this.toastr.error('An unexpected error occurred.', 'Error');
    }
  }
}
