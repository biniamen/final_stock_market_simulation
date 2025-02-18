import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms'; 
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

// Angular Material Components
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatSelectModule } from '@angular/material/select';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';  // Add this
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner'; // Add this
import { MatPaginatorModule } from '@angular/material/paginator'; // For pagination
import { MatSortModule } from '@angular/material/sort'; // For sorting
import { ToastrModule } from 'ngx-toastr';
import { AppRoutingModule } from './app-routing.module';
import { MatDialogModule } from '@angular/material/dialog';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatSnackBarModule } from '@angular/material/snack-bar'; // Import MatSnackBarModule
import { MatCheckboxModule } from '@angular/material/checkbox';


// Components

import { AppComponent } from './app.component';
import { AuthLoginComponent } from './components/auth-login/auth-login.component';
import { AuthRegisterComponent } from './components/auth-register/auth-register.component';
import { HomeComponent } from './components/home/home.component';
import { UserListComponent } from './components/user-list.component.ts/user-list.component.ts.component';
import { MatTableModule } from '@angular/material/table';
import { OrdersComponent } from './components/orders/orders.component';
import { LayoutComponent } from './layout/layout.component';
import { UserTradedComponent } from './user-traded/user-traded.component';
import { PublishStockComponent } from './components/publish-stock/publish-stock.component';
import { OtpVerificationComponent } from './components/otp-verification/otp-verification.component';
import { StockListComponent } from './components/stock-list/stock-list.component';
import { NgxPaginationModule } from 'ngx-pagination';
import { BidOrderComponent } from './components/bid-order/bid-order.component';
import { AddStockComponent } from './components/add-stock/add-stock.component';
import { DisclosureUploadComponent } from './components/disclosure-upload/disclosure-upload.component';
import { MatIconModule } from '@angular/material/icon';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { UserPortfolioComponent } from './components/user-portfolio/user-portfolio.component';
import { TradesWithOrderInfoComponent } from './components/trades-with-order-info/trades-with-order-info.component';
import { TransactionAuditListComponent } from './components/transaction-audit-list/transaction-audit-list.component';
import { SuspiciousActivitiesComponent } from './components/suspicious-activities/suspicious-activities.component';
import { RecaptchaModule } from 'ng-recaptcha';
import { AuthInterceptor } from './interceptors/auth.interceptor';
import { TradesWithOrderInfoUsingStockIDComponent } from './components/trades-with-order-info-using-stock-id/trades-with-order-info-using-stock-id.component';
import { AddDividendDialogComponent } from './components/add-dividend-dialog/add-dividend-dialog.component';
import { DividendDetailedHoldingsComponent } from './components/dividend-detailed-holdings/dividend-detailed-holdings.component';
import { DividendsComponent } from './components/dividends/dividends.component';
import { RegulationsComponent } from './components/regulations/regulations.component';
import { RegulationFormDialogComponent } from './components/regulations/regulation-form-dialog/regulation-form-dialog.component';
import { WorkingHoursComponent } from './components/working-hours/working-hours.component';
import { SuspensionsComponent } from './components/suspensions/suspensions.component';
import { ListofCompnayStocksComponent } from './components/listof-compnay-stocks/listof-compnay-stocks.component';
import { ForgotPasswordComponent } from './components/forgot-password/forgot-password.component';
import { ResetPasswordComponent } from './components/reset-password/reset-password.component';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { ListedCompaniesComponent } from './components/listed-companies/listed-companies.component';

@NgModule({
  declarations: [
    AppComponent,
    AuthLoginComponent,
    AuthRegisterComponent,
    HomeComponent,
    UserListComponent,
    OrdersComponent,
    LayoutComponent,
    UserTradedComponent,
    PublishStockComponent,
    OtpVerificationComponent,
    StockListComponent,
    BidOrderComponent,
    AddStockComponent,
    DisclosureUploadComponent,
    UserPortfolioComponent,
    TradesWithOrderInfoComponent,
    TransactionAuditListComponent,
    SuspiciousActivitiesComponent,
    TradesWithOrderInfoUsingStockIDComponent,
    AddDividendDialogComponent,
    DividendDetailedHoldingsComponent,
    DividendsComponent,
    RegulationsComponent,
    RegulationFormDialogComponent,
    WorkingHoursComponent,
    SuspensionsComponent,
    ListofCompnayStocksComponent,
    ForgotPasswordComponent,
    ResetPasswordComponent,
    ListedCompaniesComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    MatMenuModule,
    ToastrModule.forRoot({
      positionClass: 'toast-top-right',
      timeOut: 3000,
      closeButton: true,
      preventDuplicates: true
    }),
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    RecaptchaModule,
    BrowserAnimationsModule,
    MatInputModule,
    MatButtonModule,
    MatDialogModule,
    MatCardModule,
    MatProgressSpinnerModule,
    MatPaginatorModule,
    MatSortModule,
    MatSelectModule,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule, // Add this module
    AppRoutingModule,
    MatTableModule,
    NgxPaginationModule,
    MatIconModule,
    MatTooltipModule, 
    MatButtonModule,
    MatGridListModule,
    MatSnackBarModule, // Add MatSnackBarModule here
    MatExpansionModule,
    MatChipsModule,
    MatProgressBarModule,
    MatTabsModule,
    MatCheckboxModule // Add this



  ],
   providers: [
    { 
      provide: HTTP_INTERCEPTORS, 
      useClass: AuthInterceptor, 
      multi: true 
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
