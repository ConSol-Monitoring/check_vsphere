sub find_entity_view {
   my $self = &_select_vim;
   my %args = @_;
   my $service = $self->{vim_service};
   my $sc = $self->{service_content};

   if (! exists($args{view_type})) {
      Carp::confess('view_type argument is required');
   }
   my $view_type = $args{view_type};

   eval {
      VIMRuntime::load($view_type);
   };
   if ($@) {
      Carp::croak "Unable to load class '$view_type' for find_entity_view(): Perhaps it is not a valid managed entity type";
   }
   
   delete $args{view_type};
   if (! $view_type->isa('EntityViewBase')) {
      Carp::confess("$view_type is not a ManagedEntity");
   }
   my $properties = "";
   if (exists ($args{properties})) {
      if (defined($args{properties})) {
         $properties = $args{properties};
      }
      delete $args{properties};
   }
   my $begin_entity = $sc->rootFolder;
   if (exists ($args{begin_entity})) {
      $begin_entity = $args{begin_entity};
      delete $args{begin_entity};
   }   
   my $filter = {};
   if (exists ($args{filter})) {
      $filter = $args{filter};
      delete $args{filter};
   }
   
   my @remaining = keys %args;
   if (@remaining > 0) {
      Carp::confess("Unexpected argument @remaining");
   }
   my %filter_hash;
   foreach (keys %$filter) {
      my $key = $_;
      my $keyvalue = $filter->{$_};
      my $index = index($_, "-");
      if($index == 0) {
         $key = substr($key,1);
      }
      $filter_hash{$key} = $keyvalue;
   }
   my $property_spec = PropertySpec->new(all => 0,
                                         type => $view_type->get_backing_type(),
                                         pathSet => [keys %filter_hash]);

   my $service_url = $self->{service_url};
   my %result = query_api_supported($service_url);
   my $is_exists_vimversion_xml = $result{"supported"};
   my $property_filter_spec;
   if($is_exists_vimversion_xml eq '1') {
      $property_filter_spec = 
         $view_type->get_search_filter_spec_v40($begin_entity, [$property_spec], %result);
   }
   else {
      $property_filter_spec = 
         $view_type->get_search_filter_spec($begin_entity, [$property_spec]);
   }

   my $obj_contents =
      $service->RetrieveProperties(_this => $sc->propertyCollector,
                                   specSet => $property_filter_spec);   
   my $result = Util::check_fault($obj_contents);   
   my $filtered_obj;
   foreach (@$result) {
      my $obj_content = $_;
      if (keys %$filter == 0) {
         $filtered_obj = $obj_content->obj;
         last;
      }

      my %prop_hash;    
      my $prop_set = $obj_content->propSet;
      if (! $prop_set) {
         next;
      }
      foreach (@$prop_set) {
         $prop_hash{$_->name} = $_->val;
      }
      my $matched = 1;
      foreach (keys %$filter) {
         my $index = index($_, "-");
         my $regex = $filter->{$_};
         my $flag = 0;
         if($index == 0) {
            $_ = substr($_,1);
            $flag=1;
         }
         if (exists ($prop_hash{$_})) {         
            my $val;
            if (ref $prop_hash{$_}) {
               my $class = ref $prop_hash{$_};
               if ($class->isa("SimpleType")) {
                  $val = $prop_hash{$_}->val();
               } else {
                  Carp::croak("Filtering is only supported for Simple Types\n");
               }
            } else {
               $val = $prop_hash{$_};
            }
            
            if($flag == 0) {
               if (not match($regex,$val)) {
                  $matched = 0;
                  last;
               }
            }
            else {
               if (not mismatch($regex,$val)) {
                  $matched = 0;
                  last;
               }
            }
         }
      }
      if ($matched) {
         $filtered_obj = $obj_content->obj;
      }
   }
   if (! $filtered_obj) {
      return undef;
   } else {
      return $self->get_view(mo_ref => $filtered_obj,
                             view_type => $view_type,
                             properties => $properties);
   }
}
