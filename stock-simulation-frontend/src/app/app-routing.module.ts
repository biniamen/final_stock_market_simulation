import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthLoginComponent } from './components/auth-login/auth-login.component';
import { AuthRegisterComponent } from './components/auth-register/auth-register.component';
import { HomeComponent } from './components/home/home.component';
import { UserListComponent } from './components/user-list.component.ts/user-list.component.ts.component';
import { OrdersComponent } from './components/orders/orders.component';
import { AuthGuard } from './auth.guard';
import { LayoutComponent } from './layout/layout.component';
import { PublishStockComponent } from './components/publish-stock/publish-stock.component';
import { OtpVerificationComponent } from './components/otp-verification/otp-verification.component';
import { StockListComponent } from './components/stock-list/stock-list.component';
import { BidOrderComponent } from './components/bid-order/bid-order.component';
import { AddStockComponent } from './components/add-stock/add-stock.component';
import { DisclosureUploadComponent } from './components/disclosure-upload/disclosure-upload.component';
import { UserPortfolioComponent } from './components/user-portfolio/user-portfolio.component';
import { TradesWithOrderInfoComponent } from './components/trades-with-order-info/trades-with-order-info.component';
import { TransactionAuditListComponent } from './components/transaction-audit-list/transaction-audit-list.component';
import { SuspiciousActivitiesComponent } from './components/suspicious-activities/suspicious-activities.component';
import { CompanyDividendsComponent } from './components/company-dividends/company-dividends.component';
import { TradesWithOrderInfoUsingStockIDComponent } from './components/trades-with-order-info-using-stock-id/trades-with-order-info-using-stock-id.component';
import { DividendDetailedHoldingsComponent } from './components/dividend-detailed-holdings/dividend-detailed-holdings.component';
import { DividendsComponent } from './components/dividends/dividends.component';
import { RegulationsComponent } from './components/regulations/regulations.component';
import { WorkingHoursComponent } from './components/working-hours/working-hours.component';
import { SuspensionsComponent } from './components/suspensions/suspensions.component';

// const routes: Routes = [
//   { path: 'login', component: AuthLoginComponent },
//   { path: 'register', component: AuthRegisterComponent },
//   { path: 'home', component: HomeComponent },  // Add the home route
//   { path: '', redirectTo: '/login', pathMatch: 'full' } , // Default redirect to login
//   { path: 'users', component: UserListComponent },
//  // { path: '**', redirectTo: '/login' }, // Wildcard route to redirect invalid URLs to login
//   { path: 'orders', component: OrdersComponent },
//   { path: '**', redirectTo: '/orders' }, // Default to orders for testing
// ];
const routes: Routes = [
  { path: 'login', component: AuthLoginComponent }, // Public route
  { path: 'register', component: AuthRegisterComponent }, // Public route
  { path: 'otp-verification', component: OtpVerificationComponent }, // Public route for OTP verification

  {
    path: '',
    component: LayoutComponent,
    canActivate: [AuthGuard], // Protect with AuthGuard
    children: [
      { path: 'home', component: HomeComponent }, // Home page content only
      { path: 'orders', component: OrdersComponent },
      { path: 'stocks', component: StockListComponent },
      { path: 'publish-stock', component: PublishStockComponent },
      { path: 'bid-order', component: BidOrderComponent },
      { path: 'add-stock', component: AddStockComponent },
      { path: 'upload-disclosure', component: DisclosureUploadComponent },
      { path: 'users-list', component: UserListComponent },
      { path: 'portfolio', component: UserPortfolioComponent}, // Apply AuthGuard if available
      { path: 'tradingInfo', component: TradesWithOrderInfoComponent}, // Apply AuthGuard if available
      { path: 'audit-trails', component: TransactionAuditListComponent },
      { path: 'suspicious-activities', component: SuspiciousActivitiesComponent },
      { path: 'tradeInfoforStock', component: TradesWithOrderInfoUsingStockIDComponent },
      { path: 'dividends', component: DividendsComponent },
      { path: 'dividend-detailed-holdings', component: DividendDetailedHoldingsComponent },
      { path: 'regulations', component: RegulationsComponent },
      { path: 'workingHour', component: WorkingHoursComponent },
      { path: 'suspension', component: SuspensionsComponent },


      // { path: 'otp-verification', component: OtpVerificationComponent },
     // { path: 'kyc-pending', component: KycPendingComponent }, // Page after success
    ],
  },
  { path: '**', redirectTo: '/login' }, // Redirect unknown routes to login
];


@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
