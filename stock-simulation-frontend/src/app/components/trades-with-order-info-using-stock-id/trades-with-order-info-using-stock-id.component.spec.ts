import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TradesWithOrderInfoUsingStockIDComponent } from './trades-with-order-info-using-stock-id.component';

describe('TradesWithOrderInfoUsingStockIDComponent', () => {
  let component: TradesWithOrderInfoUsingStockIDComponent;
  let fixture: ComponentFixture<TradesWithOrderInfoUsingStockIDComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TradesWithOrderInfoUsingStockIDComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TradesWithOrderInfoUsingStockIDComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
