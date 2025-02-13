import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ListedCompaniesComponent } from './listed-companies.component';

describe('ListedCompaniesComponent', () => {
  let component: ListedCompaniesComponent;
  let fixture: ComponentFixture<ListedCompaniesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ListedCompaniesComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ListedCompaniesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
