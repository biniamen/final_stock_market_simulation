import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ListofCompnayStocksComponent } from './listof-compnay-stocks.component';

describe('ListofCompnayStocksComponent', () => {
  let component: ListofCompnayStocksComponent;
  let fixture: ComponentFixture<ListofCompnayStocksComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ListofCompnayStocksComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ListofCompnayStocksComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
