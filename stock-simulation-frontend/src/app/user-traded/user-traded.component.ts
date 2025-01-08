import { Component, OnInit, ViewChild } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { AuthService } from '../services/auth.service';
import { ToastrService } from 'ngx-toastr';
@Component({
  selector: 'app-user-traded',
  templateUrl: './user-traded.component.html',
  styleUrls: ['./user-traded.component.css']
})
export class UserTradedComponent implements OnInit {

  displayedColumns: string[] = ['username', 'email', 'role', 'kyc_verified', 'kyc_document', 'actions'];
  dataSource!: MatTableDataSource<any>;

  constructor(private authService: AuthService, private toastr: ToastrService,private http: HttpClient) {}
  ngOnInit(): void {
  }

  fetchOrders(): void {
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    });
  
    // this.http.get<any[]>('http://127.0.0.1:8000/api/stocks/user/orders/', { headers: headers }).subscribe(
    //   (data) => {
    //     this.dataSource.data = data;
    //     this.dataSource.paginator = this.paginator;
    //     this.dataSource.sort = this.sort;
    //     this.isLoading = false;
    //   },
    //   (error) => {
    //     console.error('Error fetching orders:', error);
    //     this.isLoading = false;
    //   }
    // );
  }
}
