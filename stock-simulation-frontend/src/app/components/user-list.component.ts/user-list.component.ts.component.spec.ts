import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UserListComponentTsComponent } from './user-list.component.ts.component';

describe('UserListComponentTsComponent', () => {
  let component: UserListComponentTsComponent;
  let fixture: ComponentFixture<UserListComponentTsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ UserListComponentTsComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(UserListComponentTsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
